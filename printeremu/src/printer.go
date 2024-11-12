package src

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/gorilla/websocket"
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
	Attributes          map[string]string
	WSConnection        *websocket.Conn
}

// DisableMotor disables a motor for a specific axis
func (printer *Printer) DisableMotor(axis string) error {
	if axis != "x" && axis != "y" && axis != "z" {
		return fmt.Errorf("invalid axis: %s. Valid axes are 'x', 'y', or 'z'", axis)
	}

	printer.EnabledMotors[axis] = false

	return nil
}

// EnableMotor enables a motor for a specific axis
func (printer *Printer) EnableMotor(axis string) error {
	if axis != "x" && axis != "y" && axis != "z" {
		return fmt.Errorf("invalid axis: %s. Valid axes are 'x', 'y', or 'z'", axis)
	}

	printer.EnabledMotors[axis] = true

	return nil
}

// AllMotorsEnabled checks if all motors are enabled
func (printer *Printer) AllMotorsEnabled() bool {
	for _, enabled := range printer.EnabledMotors {
		if !enabled {
			return false
		}
	}
	return true
}

// NewPrinter initializes a Printer with given specifications
func NewPrinter(id int, device, description, hwid, name, status, date string, extruder *Extruder, heatbed *Heatbed) (*Printer, error) {
	if extruder == nil || heatbed == nil {
		return nil, fmt.Errorf("extruder and heatbed must not be nil")
	}
	if name == "" || device == "" {
		return nil, fmt.Errorf("name and device must be provided")
	}

	printer := &Printer{
		Id:                  id,
		Device:              device,
		Description:         description,
		Hwid:                hwid,
		Name:                name,
		Status:              status,
		Date:                date,
		Extruder:            extruder,
		Heatbed:             heatbed,
		Paused:              false,
		Units:               "mm",       // Default units
		KeepAliveTime:       time.Now(), // Initialize with current time
		Acceleration:        0.0,        // Default acceleration
		Progress:            0,          // Default progress percentage
		LinearAdvanceFactor: 0.0,        // Default linear advance factor
		HeatbreakTemp:       0.0,        // Default heatbreak temp
		EnabledMotors:       make(map[string]bool),
		Attributes:          make(map[string]string),
		WSConnection:        nil, // Default will be offline emulator
	}

	return printer, nil
}

// SetUnits allows the printer to switch between mm or inches
func (printer *Printer) SetUnits(units string) error {
	if units != "mm" && units != "inches" {
		return fmt.Errorf("invalid units: %s. Supported values are 'mm' or 'inches'", units)
	}

	printer.Units = units

	return nil
}

// SetExtruderTemp sets the extruder temperature
func (printer *Printer) SetExtruderTemperature(temp float64) error {
	if temp < 0 || temp > 300 {
		return fmt.Errorf("invalid extruder temperature: %.2f°C. Valid range: 0°C to 300°C", temp)
	}

	printer.Extruder.SetExtruderTemp(temp)

	return nil
}

// GetExtruderTemp gets the extruder temperature
func (printer *Printer) GetExtruderTemp() float64 {
	return printer.Extruder.ExtruderTemp
}

// SetBedTemp sets the target bed temperature and begins heating
func (printer *Printer) SetBedTemperature(temp float64) error {
	if temp < 0 || temp > 120 {
		return fmt.Errorf("invalid bed temperature: %.2f°C. Valid range: 0°C to 120°C", temp)
	}

	printer.Heatbed.SetBedTemp(temp)

	return nil
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
func (printer *Printer) SetFanSpeed(speed float64) error {
	if speed < 0 || speed > 100 {
		return fmt.Errorf("invalid fan speed: %.2f. Valid range: 0 to 100", speed)
	}

	printer.Extruder.SetFanSpeed(speed)

	return nil
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

// UpdateProgress updates the progress of the print job
func (printer *Printer) UpdateProgress(progress int) error {
	if progress >= 0 && progress <= 100 {
		printer.Progress = progress
	} else {
		return fmt.Errorf("invalid progress: %d. Valid range: 0 to 100", progress)
	}

	return nil
}

// MoveExtruder moves the extruder to the specified position.
// It validates the position and checks if the printer is in a valid state (not paused).
func (printer *Printer) MoveExtruder(targetPos Vector3) error {
	// Ensure the printer is not paused
	if printer.Paused {
		return fmt.Errorf("cannot move extruder: printer is paused")
	}

	// Optionally, check if the position is within the allowed print area
	if targetPos.X < 0 || targetPos.Y < 0 || targetPos.Z < 0 {
		return fmt.Errorf("invalid position: coordinates cannot be negative")
	}

	// Check for the printable area bounds (example)
	if targetPos.X > printer.Heatbed.Width || targetPos.Y > printer.Heatbed.Length || targetPos.Z > printer.Extruder.MaxZHeight {
		return fmt.Errorf("position out of bounds: target exceeds printable area")
	}

	// If all checks pass, update the extruder position
	printer.Extruder.Position = targetPos
	return nil
}

func (printer *Printer) AddAttribute(key string, value string) {
	printer.Attributes[key] = value
}

func (printer *Printer) GetAttribute(key string) string {
	return printer.Attributes[key]
}

func (printer *Printer) WriteSerial(event string, data interface{}) error {
	if printer.WSConnection == nil {
		return fmt.Errorf("WebSocket connection not established")
	}

	message := map[string]interface{}{
		"event": event,
		"data":  data,
	}

	jsonMessage, err := json.Marshal(message)

	if err != nil {
		return fmt.Errorf("failed to marshal printer object: %v", err)
	}

	err = printer.WSConnection.WriteMessage(websocket.TextMessage, []byte(jsonMessage))

	if err != nil {
		return fmt.Errorf("failed to send command over WebSocket: %v", err)
	}

	return nil
}

func (printer *Printer) ReadSerial() (string, error) {
	if printer.WSConnection == nil {
		return "", fmt.Errorf("WebSocket connection not established")
	}

	_, message, err := printer.WSConnection.ReadMessage()

	if err != nil {
		return "", fmt.Errorf("failed to read message from WebSocket: %v", err)
	}

	return string(message), nil
}

// String provides a formatted string representation of the Printer state
func (printer *Printer) String() string {
	return fmt.Sprintf("Printer{Id: %d, Device: %s, Description: %s, Hwid: %s, Name: %s, Status: %s, Date: %s, Extruder: %v, Heatbed: %v, Acceleration: %.2f, LinearAdvanceFactor: %.2f, HeatbreakTemp: %.2f, Units: %s, Progress: %d%%, KeepAliveTime: %v, EnabledMotors: %v, Attributes: %v}",
		printer.Id, printer.Device, printer.Description, printer.Hwid, printer.Name, printer.Status, printer.Date, printer.Extruder.String(), printer.Heatbed.String(), printer.Acceleration, printer.LinearAdvanceFactor, printer.HeatbreakTemp, printer.Units, printer.Progress, printer.KeepAliveTime, printer.EnabledMotors, printer.Attributes)
}
