package src 

import (
	"fmt"
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
	fmt.Println("Running...")

	extruder.SetExtruderTemp(200)

	printer.GetExtruder().SetBedTemp(50)

	printer.GetExtruder().SetFanSpeed(100)

	fmt.Println(printer.String())

	fmt.Println("Done!")
}