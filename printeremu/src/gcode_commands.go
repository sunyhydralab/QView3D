package src

import (
	"fmt"
	"math"
	"regexp"
	"strconv"
	"strings"
)

type Command interface {
	Execute(printer *Printer) string
}

// CommandHandler parses and executes commands
func CommandHandler(command string, printer *Printer) string {
	command = strings.TrimSpace(command)
	cmd := NewCommand(command, printer)

	if cmd == nil {
		return "Unknown command\n"
	}
	return cmd.Execute(printer)
}

// NewCommand parses a command string and returns the appropriate Command
func NewCommand(command string, printer *Printer) Command {
	for key, factory := range commandRegistry {
		if strings.HasPrefix(command, key) {
			return factory(command, printer) // Pass command and printer
		}
	}
	return nil
}

// ==================== Movement and Positioning Commands ====================

type G28Command struct{}

func (cmd *G28Command) Execute(printer *Printer) string {
	printer.extruder.Position = Vector3{X: 0, Y: 0, Z: 0}
	return "Homing completed\n"
}

type G0G1Command struct {
	target   Vector3
	feedRate float64
}

func NewG0G1Command(command string, printer *Printer) *G0G1Command {
	target, feedRate := parseMoveCommand(command, printer.extruder.Position)
	return &G0G1Command{target: target, feedRate: feedRate}
}

func (cmd *G0G1Command) Execute(printer *Printer) string {
	if printer.paused {
		return "Printer is paused\n"
	}
	printer.extruder.Position = cmd.target
	return fmt.Sprintf("Moved to X:%.2f Y:%.2f Z:%.2f\n", cmd.target.X, cmd.target.Y, cmd.target.Z)
}

type G2G3Command struct {
	target    Vector3
	radius    float64
	clockwise bool
}

func NewG2G3Command(command string, clockwise bool, printer *Printer) *G2G3Command {
	target, radius := parseArcCommand(command, printer.extruder.Position)
	return &G2G3Command{target: target, radius: radius, clockwise: clockwise}
}

func (cmd *G2G3Command) Execute(printer *Printer) string {
	if printer.paused {
		return "Printer is paused\n"
	}
	currentPos := printer.extruder.Position
	arcAngle := 180.0
	angleRad := arcAngle * math.Pi / 180.0

	if cmd.clockwise {
		cmd.target.X = currentPos.X + cmd.radius*math.Cos(angleRad)
		cmd.target.Y = currentPos.Y - cmd.radius*math.Sin(angleRad)
	} else {
		cmd.target.X = currentPos.X - cmd.radius*math.Cos(angleRad)
		cmd.target.Y = currentPos.Y + cmd.radius*math.Sin(angleRad)
	}
	printer.extruder.Position = cmd.target

	return fmt.Sprintf("Arc move to X:%.2f Y:%.2f Z:%.2f\n", cmd.target.X, cmd.target.Y, cmd.target.Z)
}

type G4Command struct {
	duration int
}

func NewG4Command(command string) *G4Command {
	duration := parseDuration(command)
	return &G4Command{duration: duration}
}

func (cmd *G4Command) Execute(printer *Printer) string {
	return fmt.Sprintf("Dwelling for %d ms\n", cmd.duration)
}

// ==================== Positioning Commands ====================

type G90Command struct{}

func (cmd *G90Command) Execute(printer *Printer) string {
	printer.extruder.AbsolutePositioning = true
	return "Set to Absolute Positioning\n"
}

type G91Command struct{}

func (cmd *G91Command) Execute(printer *Printer) string {
	printer.extruder.AbsolutePositioning = false
	return "Set to Relative Positioning\n"
}

type G92Command struct {
	position Vector3
}

func NewG92Command(command string) *G92Command {
	position, _ := parseMoveCommand(command, Vector3{0, 0, 0})
	return &G92Command{position: position}
}

func (cmd *G92Command) Execute(printer *Printer) string {
	printer.extruder.Position = cmd.position
	return fmt.Sprintf("Position set to X:%.2f Y:%.2f Z:%.2f\n", cmd.position.X, cmd.position.Y, cmd.position.Z)
}

// ==================== Unit Conversion Commands ====================

type G20Command struct{}

func (cmd *G20Command) Execute(printer *Printer) string {
	printer.units = "inches"
	return "Units set to inches\n"
}

type G21Command struct{}

func (cmd *G21Command) Execute(printer *Printer) string {
	printer.units = "mm"
	return "Units set to millimeters\n"
}

// ==================== Temperature and Fan Control Commands ====================

type M104Command struct {
	temperature float64
}

func NewM104Command(command string) *M104Command {
	temperature := parseTemperature(command)
	return &M104Command{temperature: temperature}
}

func (cmd *M104Command) Execute(printer *Printer) string {
	printer.extruder.TargetTemp = cmd.temperature
	return fmt.Sprintf("Extruder temperature set to %.2f\n", cmd.temperature)
}

type M106Command struct {
	fanSpeed float64
}

func NewM106Command(command string) *M106Command {
	fanSpeed := parseFanSpeed(command)
	return &M106Command{fanSpeed: fanSpeed}
}

func (cmd *M106Command) Execute(printer *Printer) string {
	printer.extruder.FanSpeed = cmd.fanSpeed
	return fmt.Sprintf("Fan speed set to %.2f\n", cmd.fanSpeed)
}

type M107Command struct{}

func (cmd *M107Command) Execute(printer *Printer) string {
	printer.extruder.FanSpeed = 0.0
	return "Fan turned off\n"
}

type M140Command struct {
	temperature float64
}

func NewM140Command(command string) *M140Command {
	temperature := parseTemperature(command)
	return &M140Command{temperature: temperature}
}

func (cmd *M140Command) Execute(printer *Printer) string {
	printer.heatbed.TargetTemp = cmd.temperature
	return fmt.Sprintf("Bed temperature set to %.2f\n", cmd.temperature)
}

// ==================== Control and Status Commands ====================

type CancelCommand struct{}

func (cmd *CancelCommand) Execute(printer *Printer) string {
	printer.paused = true
	return "Emergency stop activated, printer paused\n"
}

type M114Command struct{}

func (cmd *M114Command) Execute(printer *Printer) string {
	position := printer.extruder.Position
	return fmt.Sprintf("X:%.2f Y:%.2f Z:%.2f\n", position.X, position.Y, position.Z)
}

type M997Command struct{}

func (cmd *M997Command) Execute(printer *Printer) string {
	return fmt.Sprintf("Machine name: %s", printer.device)
}

type M601Command struct{}

func (cmd *M601Command) Execute(printer *Printer) string {
	if printer.paused {
		return "Printer is already paused\n"
	}
	printer.paused = true
	return "Machine is paused\n"
}

type M602Command struct{}

func (cmd *M602Command) Execute(printer *Printer) string {
	if !printer.paused {
		return "Printer is not paused\n"
	}
	printer.paused = false
	return "Machine is no longer paused\n"
}

// ==================== Parsing Helpers ====================

func parseMoveCommand(command string, currentPos Vector3) (Vector3, float64) {
	reX := regexp.MustCompile(`X([-+]?[0-9]*\.?[0-9]+)`)
	reY := regexp.MustCompile(`Y([-+]?[0-9]*\.?[0-9]+)`)
	reZ := regexp.MustCompile(`Z([-+]?[0-9]*\.?[0-9]+)`)
	reF := regexp.MustCompile(`F([-+]?[0-9]*\.?[0-9]+)`)

	target := currentPos
	feedRate := 3600.0

	if xMatch := reX.FindStringSubmatch(command); xMatch != nil {
		target.X, _ = strconv.ParseFloat(xMatch[1], 64)
	}
	if yMatch := reY.FindStringSubmatch(command); yMatch != nil {
		target.Y, _ = strconv.ParseFloat(yMatch[1], 64)
	}
	if zMatch := reZ.FindStringSubmatch(command); zMatch != nil {
		target.Z, _ = strconv.ParseFloat(zMatch[1], 64)
	}
	if fMatch := reF.FindStringSubmatch(command); fMatch != nil {
		feedRate, _ = strconv.ParseFloat(fMatch[1], 64)
	}

	return target, feedRate
}

func parseArcCommand(command string, currentPos Vector3) (Vector3, float64) {
	reR := regexp.MustCompile(`R([-+]?[0-9]*\.?[0-9]+)`)
	radius := 0.0
	target := currentPos

	if rMatch := reR.FindStringSubmatch(command); rMatch != nil {
		radius, _ = strconv.ParseFloat(rMatch[1], 64)
	}
	return target, radius
}

func parseDuration(command string) int {
	reP := regexp.MustCompile(`P([0-9]+)`)
	duration := 0

	if pMatch := reP.FindStringSubmatch(command); pMatch != nil {
		duration, _ = strconv.Atoi(pMatch[1])
	}
	return duration
}

func parseTemperature(command string) float64 {
	reS := regexp.MustCompile(`S([-+]?[0-9]*\.?[0-9]+)`)
	temperature := 0.0

	if sMatch := reS.FindStringSubmatch(command); sMatch != nil {
		temperature, _ = strconv.ParseFloat(sMatch[1], 64)
	}
	return temperature
}

func parseFanSpeed(command string) float64 {
	reS := regexp.MustCompile(`S([-+]?[0-9]*\.?[0-9]+)`)
	fanSpeed := 0.0

	if sMatch := reS.FindStringSubmatch(command); sMatch != nil {
		fanSpeed, _ = strconv.ParseFloat(sMatch[1], 64)
	}
	return fanSpeed
}

// ==================== Command Registry ====================

var commandRegistry = map[string]func(string, *Printer) Command{
	"G28":  func(cmd string, p *Printer) Command { return &G28Command{} },
	"G0":   func(cmd string, p *Printer) Command { return NewG0G1Command(cmd, p) },
	"G1":   func(cmd string, p *Printer) Command { return NewG0G1Command(cmd, p) },
	"G2":   func(cmd string, p *Printer) Command { return NewG2G3Command(cmd, true, p) },
	"G3":   func(cmd string, p *Printer) Command { return NewG2G3Command(cmd, false, p) },
	"G4":   func(cmd string, p *Printer) Command { return NewG4Command(cmd) },
	"G20":  func(cmd string, p *Printer) Command { return &G20Command{} },
	"G21":  func(cmd string, p *Printer) Command { return &G21Command{} },
	"G90":  func(cmd string, p *Printer) Command { return &G90Command{} },
	"G91":  func(cmd string, p *Printer) Command { return &G91Command{} },
	"G92":  func(cmd string, p *Printer) Command { return NewG92Command(cmd) },
	"M104": func(cmd string, p *Printer) Command { return NewM104Command(cmd) },
	"M106": func(cmd string, p *Printer) Command { return NewM106Command(cmd) },
	"M107": func(cmd string, p *Printer) Command { return &M107Command{} },
	"M112": func(cmd string, p *Printer) Command { return &CancelCommand{} },
	"M114": func(cmd string, p *Printer) Command { return &M114Command{} },
	"M140": func(cmd string, p *Printer) Command { return NewM140Command(cmd) },
	"M190": func(cmd string, p *Printer) Command { return NewM140Command(cmd) },
	"M601": func(cmd string, p *Printer) Command { return &M601Command{} },
	"M602": func(cmd string, p *Printer) Command { return &M602Command{} },
	"M997": func(cmd string, p *Printer) Command { return &M997Command{} },
}
