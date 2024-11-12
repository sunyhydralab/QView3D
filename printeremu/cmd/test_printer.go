package main

import (
	"bufio"
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"

	"printeremu/src"
)

func main() {
	printers, err := src.LoadPrinters("data/printers.json")

	if err != nil {
		log.Fatalf("Error loading printers: %v", err)
	}

	fmt.Println("Loaded printers...")

	var printer *src.Printer

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

			handleConnection(extruder, printer)

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

func handleConnection(extruder *src.Extruder, printer *src.Printer) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-signalChan
		cancel()
	}()

	go func() {
		src.RunConnection(ctx, extruder, printer)
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
