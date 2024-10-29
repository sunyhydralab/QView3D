package src 

import (
	"fmt"
	"time"
)

func main() {

}

func Init() error {
	// TODO: add!

	fmt.Println("Reading up...")

	// Correctly create a Vector3 instance
	position := Vector3{X: 100, Y: 27, Z: 76}
	extruder := NewExtruder(position, 250, 100, 125) // Use the Vector3
	
	// Create a new Printer instance
	printer := NewPrinter(0, "Ender3", "Creality Brand", "Hwid", "Test Ender3", "Init", time.Now().String(), extruder)

	fmt.Println(printer.String())
	
	return nil
}

func Run() {
	fmt.Println("Hello world!")
}