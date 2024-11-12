package main

import (
	"bufio"
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"printeremu/src"
)

func main() {
	extruder, printer, err := src.Init(1, "Generic", "Marlin GCode", "EMU032uhb3293n2", "Testing Printer 1", "Init")

	if err != nil {
		fmt.Println("Error initializing printer:", err)
		return
	}

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

		if strings.ToLower(command) == "command" {
			fmt.Println("Running command emulator...")

			handleCommand(extruder, printer)

			break
		}

		if strings.ToLower(command) == "connection" {
			fmt.Println("Running command emulator...")

			handleConnection(extruder, printer)

			break
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
