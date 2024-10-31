package src

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"strings"
	"time"
)

// Main function to initialize and run the printer emulator
func main() {
	extruder, printer, err := Init(1, "Device1", "Test Printer", "HWID1234", "Printer1", "Active")
	if err != nil {
		log.Fatalf("Failed to initialize printer: %v", err)
	}
	Run(extruder, printer)
}

// Init function initializes the Extruder and Printer
func Init(id int, device string, description string, hwid string, name string, status string) (*Extruder, *Printer, error) {
	fmt.Println("Initializing printer...")

	position := Vector3{X: 100, Y: 27, Z: 76}
	extruder := NewExtruder(position, 250, 100, 125)

	// Create a new heatbed instance
	heatbed := &Heatbed{
		Temp:       60.0, // Default initial temperature
		TargetTemp: 100.0, // Target temperature for the heatbed
	}

	printer := NewPrinter(id, device, description, hwid, name, status, time.Now().String(), extruder, heatbed)

	fmt.Println(printer.String())

	return extruder, printer, nil
}

// Run function for G-code command input and processing
func Run(extruder *Extruder, printer *Printer) {
	scanner := bufio.NewScanner(os.Stdin)

	fmt.Println("Enter G-code commands (type 'exit' or 'quit' to quit):")

	for {
		fmt.Print("> ")
		scanner.Scan()
		command := scanner.Text()

		if strings.ToLower(command) == "exit" || strings.ToLower(command) == "quit" {
			fmt.Println("Exiting printer emulator...")
			break
		}

		response := CommandHandler(command, printer)
		fmt.Println(response)
	}

	if err := scanner.Err(); err != nil {
		log.Println("Error reading input:", err)
	}
}
