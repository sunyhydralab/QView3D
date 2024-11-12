package src

import (
	"fmt"
	"math"
	"regexp"
	"strconv"
	"strings"
	"time"
)

type Command interface {
	Execute(printer *Printer) string
}

// CommandHandler parses and executes commands
func CommandHandler(command string, printer *Printer) string {
	if semicolonIndex := strings.Index(command, ";"); semicolonIndex != -1 {
		command = command[:semicolonIndex]
	}

	if command == "" {
		return ""
	}

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
			return factory(command, printer)
		}
	}
	return nil
}

// ==================== Movement and Positioning Commands ====================

type G28Command struct{}

func (cmd *G28Command) Execute(printer *Printer) string {
	if err := printer.MoveExtruder(Vector3{X: 0, Y: 0, Z: 0}); err != nil {
		return fmt.Sprintf("Error: %s\n", err.Error())
	}

	return "Homing completed\n"
}

type G0G1Command struct {
	target   Vector3
	feedRate float64
}

func NewG0G1Command(command string, printer *Printer) *G0G1Command {
	target, feedRate := parseMoveCommand(command, printer.Extruder.Position)

	return &G0G1Command{target: target, feedRate: feedRate}
}

func (cmd *G0G1Command) Execute(printer *Printer) string {
	// TODO: Implement feed rate
	if err := printer.MoveExtruder(cmd.target); err != nil {
		return fmt.Sprintf("Error: %s\n", err.Error())
	}

	return fmt.Sprintf("Moved to X:%.2f Y:%.2f Z:%.2f\n", cmd.target.X, cmd.target.Y, cmd.target.Z)
}

type G2G3Command struct {
	target    Vector3
	radius    float64
	clockwise bool
}

func NewG2G3Command(command string, clockwise bool, printer *Printer) *G2G3Command {
	target, radius := parseArcCommand(command, printer.Extruder.Position)

	return &G2G3Command{target: target, radius: radius, clockwise: clockwise}
}

func (cmd *G2G3Command) Execute(printer *Printer) string {
	if printer.Paused {
		return "Printer is paused\n"
	}

	currentPos := printer.Extruder.Position
	arcAngle := 180.0
	angleRad := arcAngle * math.Pi / 180.0

	if cmd.clockwise {
		cmd.target.X = currentPos.X + cmd.radius*math.Cos(angleRad)
		cmd.target.Y = currentPos.Y - cmd.radius*math.Sin(angleRad)
	} else {
		cmd.target.X = currentPos.X - cmd.radius*math.Cos(angleRad)
		cmd.target.Y = currentPos.Y + cmd.radius*math.Sin(angleRad)
	}

	if err := printer.MoveExtruder(cmd.target); err != nil {
		return fmt.Sprintf("Error: %s\n", err.Error())
	}

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

type G90Command struct{}

func (cmd *G90Command) Execute(printer *Printer) string {
	printer.Extruder.AbsolutePositioning = true

	return "Set to Absolute Positioning\n"
}

type G91Command struct{}

func (cmd *G91Command) Execute(printer *Printer) string {
	printer.Extruder.AbsolutePositioning = false

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
	if err := printer.MoveExtruder(cmd.position); err != nil {
		return fmt.Sprintf("Error: %s\n", err.Error())
	}

	return fmt.Sprintf("Position set to X:%.2f Y:%.2f Z:%.2f\n", cmd.position.X, cmd.position.Y, cmd.position.Z)
}

// ==================== Unit Conversion Commands ====================

type G20Command struct{}

func (cmd *G20Command) Execute(printer *Printer) string {
	printer.Units = "inches"
	return "Units set to inches\n"
}

type G21Command struct{}

func (cmd *G21Command) Execute(printer *Printer) string {
	printer.Units = "mm"
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
	if err := printer.SetExtruderTemperature(cmd.temperature); err != nil {
		return fmt.Sprintf("Error: %s\n", err.Error())
	}

	return fmt.Sprintf("Extruder temperature set to %.2f°C\n", cmd.temperature)
}

type M106Command struct {
	fanSpeed float64
}

func NewM106Command(command string) *M106Command {
	fanSpeed := parseFanSpeed(command)

	return &M106Command{fanSpeed: fanSpeed}
}

func (cmd *M106Command) Execute(printer *Printer) string {
	if err := printer.SetFanSpeed(cmd.fanSpeed); err != nil {
		return fmt.Sprintf("Error: %s\n", err.Error())
	}

	return fmt.Sprintf("Fan speed set to %.2f\n", cmd.fanSpeed)
}

type M107Command struct{}

func (cmd *M107Command) Execute(printer *Printer) string {
	printer.SetFanSpeed(0)

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
	// Set the target temperature of the bed, but do not block
	if err := printer.SetBedTemperature(cmd.temperature); err != nil {
		return fmt.Sprintf("Error: %s\n", err.Error())
	}

	printer.Heatbed.Heating = true // Start heating

	return fmt.Sprintf("Bed temperature set to %.2f, heating in progress\n", cmd.temperature)
}

// M190Command waits until the bed reaches the target temperature before allowing further commands
type M190Command struct {
	temperature float64
}

func NewM190Command(command string) *M190Command {
	temperature := parseTemperature(command)

	return &M190Command{temperature: temperature}
}

func (cmd *M190Command) Execute(printer *Printer) string {
	// Set the target temperature and check if the bed is heated
	// TODO: use error handling!
	printer.Heatbed.TargetTemp = cmd.temperature

	// Check if the current temperature is below the target
	if printer.Heatbed.Temp < printer.Heatbed.TargetTemp {
		return "Waiting for bed to reach target temperature...\n"
	}

	// If target temperature reached, continue
	printer.Heatbed.Heating = false
	return fmt.Sprintf("Bed temperature reached %.2f\n", cmd.temperature)
}

type M113Command struct{}

func NewM113Command(command string) *M113Command {
	return &M113Command{}
}

func (cmd *M113Command) Execute(printer *Printer) string {
	printer.KeepAliveTime = time.Now()
	return "Keepalive signal sent\n"
}

type M204Command struct {
	acceleration float64
}

func NewM204Command(command string) *M204Command {
	acceleration := parseAcceleration(command)
	return &M204Command{acceleration: acceleration}
}

func (cmd *M204Command) Execute(printer *Printer) string {
	printer.Acceleration = cmd.acceleration
	return fmt.Sprintf("Acceleration set to %.2f\n", cmd.acceleration)
}

type M73Command struct {
	progress int
}

func NewM73Command(command string) *M73Command {
	progress := parseProgress(command)

	return &M73Command{progress: progress}
}

func (cmd *M73Command) Execute(printer *Printer) string {
	printer.UpdateProgress(cmd.progress)

	return fmt.Sprintf("Progress set to %d%%\n", cmd.progress)
}

// ==================== Control and Status Commands ====================

type CancelCommand struct{}

func (cmd *CancelCommand) Execute(printer *Printer) string {
	printer.Pause()

	return "Emergency stop activated, printer paused\n"
}

type M114Command struct{}

func (cmd *M114Command) Execute(printer *Printer) string {
	position := printer.Extruder.Position
	return fmt.Sprintf("X:%.2f Y:%.2f Z:%.2f\n", position.X, position.Y, position.Z)
}

type M997Command struct{}

func (cmd *M997Command) Execute(printer *Printer) string {
	return fmt.Sprintf("Machine name: %s", printer.Device)
}

type M601Command struct{}

func (cmd *M601Command) Execute(printer *Printer) string {
	printer.Pause()

	return "Printer paused\n"
}

type M602Command struct{}

func (cmd *M602Command) Execute(printer *Printer) string {
	printer.Resume()

	return "Printer not paused\n"
}

type M900Command struct {
	kFactor float64
}

func NewM900Command(command string) *M900Command {
	kFactor := parseKFactor(command) // Extracts the K value from the command

	return &M900Command{kFactor: kFactor}
}

func (cmd *M900Command) Execute(printer *Printer) string {
	printer.LinearAdvanceFactor = cmd.kFactor

	return fmt.Sprintf("Linear Advance factor set to %.2f\n", cmd.kFactor)
}

type M142Command struct {
	temperature float64
}

func NewM142Command(command string) *M142Command {
	temperature := parseTemperature(command) // Uses parseTemperature to get S value

	return &M142Command{temperature: temperature}
}

func (cmd *M142Command) Execute(printer *Printer) string {
	printer.HeatbreakTemp = cmd.temperature

	return fmt.Sprintf("Heatbreak target temperature set to %.2f\n", cmd.temperature)
}

type M84Command struct {
	axes []string
}

func NewM84Command(command string) *M84Command {
	axes := parseAxes(command) // Extracts axes (X, Y, Z, E) from the command

	return &M84Command{axes: axes}
}

func (cmd *M84Command) Execute(printer *Printer) string {
	for _, axis := range cmd.axes {
		printer.DisableMotor(axis)
	}

	return fmt.Sprintf("Motors %v disabled\n", cmd.axes)
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

func parseAcceleration(command string) float64 {
	reS := regexp.MustCompile(`S([-+]?[0-9]*\.?[0-9]+)`)
	acceleration := 0.0

	if sMatch := reS.FindStringSubmatch(command); sMatch != nil {
		acceleration, _ = strconv.ParseFloat(sMatch[1], 64)
	}

	return acceleration
}

func parseProgress(command string) int {
	reS := regexp.MustCompile(`S([0-9]+)`)
	progress := 0

	if sMatch := reS.FindStringSubmatch(command); sMatch != nil {
		progress, _ = strconv.Atoi(sMatch[1])
	}

	return progress
}

func parseKFactor(command string) float64 {
	reK := regexp.MustCompile(`K([-+]?[0-9]*\.?[0-9]+)`)
	kFactor := 0.0

	if kMatch := reK.FindStringSubmatch(command); kMatch != nil {
		kFactor, _ = strconv.ParseFloat(kMatch[1], 64)
	}

	return kFactor
}

func parseAxes(command string) []string {
	reAxes := regexp.MustCompile(`[XYZE]`)

	return reAxes.FindAllString(command, -1)
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
	"M113": func(cmd string, p *Printer) Command { return &M113Command{} },
	"M114": func(cmd string, p *Printer) Command { return &M114Command{} },
	"M140": func(cmd string, p *Printer) Command { return NewM140Command(cmd) },
	"M190": func(cmd string, p *Printer) Command { return NewM190Command(cmd) },
	"M204": func(cmd string, p *Printer) Command { return NewM204Command(cmd) },
	"M73":  func(cmd string, p *Printer) Command { return NewM73Command(cmd) },
	"M601": func(cmd string, p *Printer) Command { return &M601Command{} },
	"M602": func(cmd string, p *Printer) Command { return &M602Command{} },
	"M997": func(cmd string, p *Printer) Command { return &M997Command{} },
	"M900": func(cmd string, p *Printer) Command { return NewM900Command(cmd) },
	"M142": func(cmd string, p *Printer) Command { return NewM142Command(cmd) },
	"M84":  func(cmd string, p *Printer) Command { return NewM84Command(cmd) },
}