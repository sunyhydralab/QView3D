package src

import (
	"fmt"
	"time"
)

// Printer struct with associated components as pointers for easy modification
type Printer struct {
	Id                  int
	Device              string
	Description         string
	Hwid                string
	Name                string
	Status              string
	Date                string
	Extruder            *Extruder
	Heatbed             *Heatbed
	Paused              bool
	Units               string
	KeepAliveTime       time.Time
	Acceleration        float64
	Progress            int
	LinearAdvanceFactor float64
	HeatbreakTemp       float64
	EnabledMotors       map[string]bool
}

func (printer *Printer) DisableMotor(axis string) {
	if printer.EnabledMotors == nil {
		printer.EnabledMotors = make(map[string]bool)
	}
	printer.EnabledMotors[axis] = false
}

// NewPrinter initializes a Printer with given specifications
func NewPrinter(id int, device, description, hwid, name, status, date string, extruder *Extruder, heatbed *Heatbed) *Printer {
	return &Printer{
		Id:            id,
		Device:        device,
		Description:   description,
		Hwid:          hwid,
		Name:          name,
		Status:        status,
		Date:          date,
		Extruder:      extruder,
		Heatbed:       heatbed,
		Paused:        false,
		Units:         "mm",       // Default units
		KeepAliveTime: time.Now(), // Initialize with current time
		Acceleration:  0.0,        // Default acceleration
		Progress:      0,          // Default progress percentage
	}
}

// SetExtruderTemp sets the extruder temperature
func (printer *Printer) SetExtruderTemp(temp float64) {
	printer.Extruder.SetExtruderTemp(temp)
}

// GetExtruderTemp gets the extruder temperature
func (printer *Printer) GetExtruderTemp() float64 {
	return printer.Extruder.ExtruderTemp
}

// SetBedTemp sets the target bed temperature and begins heating
func (printer *Printer) SetBedTemp(temp float64) {
	printer.Heatbed.SetBedTemp(temp)
}

// GetBedTemp gets the current bed temperature
func (printer *Printer) GetBedTemp() float64 {
	return printer.Heatbed.Temp
}

// UpdateBedTemperature updates the current temperature of the bed
func (printer *Printer) UpdateBedTemperature(currentTemp float64) {
	printer.Heatbed.Temp = currentTemp
	if printer.Heatbed.Temp >= printer.Heatbed.TargetTemp {
		printer.Heatbed.Heating = false
	}
}

// SetFanSpeed sets the fan speed on the extruder
func (printer *Printer) SetFanSpeed(speed float64) {
	printer.Extruder.SetFanSpeed(speed)
}

// GetFanSpeed gets the current fan speed on the extruder
func (printer *Printer) GetFanSpeed() float64 {
	return printer.Extruder.FanSpeed
}

// Pause pauses the printer
func (printer *Printer) Pause() {
	printer.Paused = true
}

// Resume resumes the printer operation
func (printer *Printer) Resume() {
	printer.Paused = false
}

// String provides a formatted string representation of the Printer state
func (printer *Printer) String() string {
	return fmt.Sprintf("Printer{Id: %d, Device: %s, Description: %s, Hwid: %s, Name: %s, Status: %s, Date: %s, Extruder: %v, Heatbed: %v, Acceleration: %.2f, Progress: %d%%, KeepAliveTime: %v}",
		printer.Id, printer.Device, printer.Description, printer.Hwid, printer.Name, printer.Status, printer.Date, printer.Extruder.String(), printer.Heatbed.String(), printer.Acceleration, printer.Progress, printer.KeepAliveTime)
}
