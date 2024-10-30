package src

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"strings"
	"time"
)

func main() {

}

func Init(id int, device string, description string, hwid string, name string, status string) (*Extruder, *Printer, error) {
	// TODO: add!
	fmt.Println("Reading up...")

	position := Vector3{X: 100, Y: 27, Z: 76}
	extruder := NewExtruder(position, 250, 100, 125)

	printer := NewPrinter(id, device, description, hwid, name, status, time.Now().String(), extruder)

	fmt.Println(printer.String())

	return extruder, printer, nil
}

func Run(extruder *Extruder, printer *Printer) {
	scanner := bufio.NewScanner(os.Stdin)

	fmt.Println("Enter G-code commands (type 'exit' to quit):")

	for {
		fmt.Print("> ")
		scanner.Scan()
		command := scanner.Text()

		if strings.ToLower(command) == "exit" {
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