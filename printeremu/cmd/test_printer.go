pythpackage main

import (
	"bufio"
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"

	"printeremu/src"
)

func getDataFilePath(filename string) string {
	// Get the current working directory
	wd, err := os.Getwd()
	if err != nil {
		log.Fatalf("Error getting working directory: %v", err)
	}

	if filepath.Base(wd) == "cmd" {
		// Go up one level to the root project directory
		wd = filepath.Dir(wd)
	}

	// Construct the absolute path to the file
	return filepath.Join(wd, "data", filename)
}

func main() {
	settingsFilePath := getDataFilePath("settings.json")
	printersFilePath := getDataFilePath("printers.json")

	settings, err := src.LoadSettings(settingsFilePath)
	if err != nil {
		log.Fatalf("Error loading settings: %v", err)
	}

	printers, err := src.LoadPrinters(printersFilePath)
	if err != nil {
		log.Fatalf("Error loading printers: %v", err)
	}

	fmt.Println("Loaded printers...")

	var printer *src.Printer // Declare this once

	if len(os.Args) == 3 { // Check if both arguments are provided
		printerID, err := strconv.Atoi(os.Args[1])
		if err != nil {
			log.Fatalf("Invalid printer ID: %v", err)
		}

		// Find the printer by ID
		for _, p := range printers {
			if p.Id == printerID {
				printer = &p
				break
			}
		}

		if printer == nil {
			log.Fatalf("Printer with ID %d not found.", printerID)
		}

		// Now we can safely access the printer.Extruder
		extruder := printer.Extruder

		// Parse the command
		command := os.Args[2]

		if command == "-conn" {
			handleConnection(extruder, printer, &settings)
			return
		}

		if command == "-comm" {
			handleCommand(extruder, printer)
			return
		}

		if command == "-reg" {
			src.PrintPrinters(printers)
			return
		}

		log.Fatalf("Unknown command: %s", command)
		return
	}

	// If no arguments, let the user choose a printer interactively
	for printer == nil {
		printer = askForPrinterID(printers)
	}

	extruder := printer.Extruder

	scanner := bufio.NewScanner(os.Stdin)

	fmt.Println("Choose command or connection for emulator (type 'exit' or 'quit' to quit):")

	for {
		fmt.Print("$ ")
		scanner.Scan()
		command := scanner.Text()

		if strings.ToLower(command) == "exit" || strings.ToLower(command) == "quit" {
			fmt.Println("Exiting printer emulator...")
			break
		}

		if strings.ToLower(command) == "command" || strings.ToLower(command) == "comm" {
			fmt.Println("Running command emulator...")

			handleCommand(extruder, printer)

			break
		}

		if strings.ToLower(command) == "connection" || strings.ToLower(command) == "conn" {
			fmt.Println("Running connection emulator...")

			handleConnection(extruder, printer, &settings)

			break
		}

		if strings.ToLower(command) == "registry" {
			fmt.Println("Printer registry...")

			src.PrintPrinters(printers)
		}
	}

	if err := scanner.Err(); err != nil {
		log.Println("Error reading input:", err)
	}
}

func handleConnection(extruder *src.Extruder, printer *src.Printer, settings *src.EmulatorSettings) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-signalChan
		cancel()
	}()

	go func() {
		src.RunConnection(ctx, extruder, printer, settings)
	}()

	<-ctx.Done()
	log.Println("Shutting down...")
}

func handleCommand(extruder *src.Extruder, printer *src.Printer) {
	src.RunCommand(extruder, printer)
}

func askForPrinterID(printers []src.Printer) *src.Printer {
	scanner := bufio.NewScanner(os.Stdin)

	for {
		fmt.Println("Available printers:")

		for _, p := range printers {
			fmt.Printf("ID: %d, Name: %s\n", p.Id, p.Name)
		}

		fmt.Print("Enter the printer ID: ")

		scanner.Scan()
		idInput := scanner.Text()

		if idInput == "exit" || idInput == "quit" {
			fmt.Println("Exiting printer emulator...")
			os.Exit(0)
		}

		id, err := strconv.Atoi(idInput)

		if err != nil {
			fmt.Println("Invalid input, please enter a valid number.")
			continue
		}

		for _, p := range printers {
			if p.Id == id {
				fmt.Printf("Selected printer: %s (ID: %d)\n", p.Name, p.Id)
				return &p
			}
		}

		fmt.Println("Printer with that ID doesn't exist. Please try again.")
	}
}
