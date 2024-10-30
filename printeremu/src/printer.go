package src

import (
	"fmt"
	"math"
	"strings"
	"time"
)

type Printer struct {
	id          int
	device      string
	description string
	hwid        string
	name        string
	status      string
	date        string
	extruder    *Extruder // Keep this as a pointer
	paused      bool
}

func NewPrinter(id int, device, description, hwid, name, status, date string, extruder *Extruder) *Printer {
	return &Printer{
		id:          id,
		device:      device,
		description: description,
		hwid:        hwid,
		name:        name,
		status:      status,
		date:        date,
		extruder:    extruder,
		paused:      false,
	}
}

func (printer *Printer) SetExtruderTemp(temp float64) {
	printer.extruder.SetExtruderTemp(temp)
}

func (printer *Printer) GetExtruderTemp() float64 {
	return printer.extruder.ExtruderTemp
}

func (printer *Printer) GetExtruder() *Extruder {
	return printer.extruder
}

func (printer *Printer) SetBedTemp(temp float64) {
	printer.extruder.SetBedTemp(temp)
}

func (printer *Printer) GetBedTemp() float64 {
	return printer.extruder.BedTemp
}

func (printer *Printer) SetFanSpeed(speed float64) {
	printer.extruder.SetFanSpeed(speed)
}

func (printer *Printer) GetFanSpeed() float64 {
	return printer.extruder.FanSpeed
}

func (printer *Printer) Pause() {
	printer.paused = true
}

func (printer *Printer) Resume() {
	printer.paused = false
}

func (printer *Printer) String() string {
	return fmt.Sprintf("Printer{Id: %d, Device: %s, Description: %s, Hwid: %s, Name: %s, Status: %s, Date: %s, Extruder: %v}",
		printer.id, printer.device, printer.description, printer.hwid, printer.name, printer.status, printer.date, printer.extruder.String())
}

func (extruder *Extruder) moveExtruder(target Vector3, feedRate float64) {
	// distance to move
	distance := math.Sqrt(math.Pow(target.X-extruder.Position.X, 2) + math.Pow(target.Y-extruder.Position.Y, 2) + math.Pow(target.Z-extruder.Position.Z, 2))

	// time taken for movement based on feed rate
	moveTime := distance / feedRate
	time.Sleep(time.Duration(moveTime*1000) * time.Millisecond) // movement delay

	extruder.Position = target
}

func CommandHandler(command string, printer *Printer) string {
	command = strings.TrimSpace(command)
	cmd := NewCommand(command, printer)

	if cmd == nil {
		return "Unknown command\n"
	}
	return cmd.Execute(printer)
}
