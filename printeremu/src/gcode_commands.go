package src

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

type Command interface {
	Execute(printer *Printer) string
}

type G28Command struct{}

func (cmd *G28Command) Execute(printer *Printer) string {
	printer.extruder.Position = Vector3{X: 0, Y: 0, Z: 0}
	return "ok\n"
}

type G0G1Command struct {
	target   Vector3
	feedRate float64
}

func (cmd *G0G1Command) Execute(printer *Printer) string {
	if (printer.paused) {
		return "Printer is paused\n"
	}

	printer.extruder.moveExtruder(cmd.target, cmd.feedRate)
	return fmt.Sprintf("Moved to X:%.2f Y:%.2f Z:%.2f\n", cmd.target.X, cmd.target.Y, cmd.target.Z)
}

type CancelCommand struct{}

func (cmd *CancelCommand) Execute(printer *Printer) string {
	// todo: logic to cancel the operation
	return "Canceled\n"
}

type KeepAliveCommand struct {
	state bool
}

func (cmd *KeepAliveCommand) Execute(printer *Printer) string {
	if cmd.state {
		// todo: Logic to enable keep-alive
		return "Keep-Alive Enabled\n"
	}
	// todo: Logic to disable keep-alive
	return "Keep-Alive Disabled\n"
}

type M114Command struct{}

func (cmd *M114Command) Execute(printer *Printer) string {
	position := printer.extruder.Position
	return fmt.Sprintf("X:%.2f Y:%.2f Z:%.2f\n", position.X, position.Y, position.Z)
}

type M997Command struct {}

func (cmd *M997Command) Execute(printer *Printer) string {
	return fmt.Sprintf("Machine name: %s", printer.device)
}

type M601Command struct {}

func (cmd *M601Command) Execute(printer *Printer) string {
	if (printer.paused) {
		return "Printer is already paused\n"
	}

	printer.paused = true
	return "Machine is paused\n"
}

type M602Command struct {}

func (cmd *M602Command) Execute(printer *Printer) string {
	if (!printer.paused) {
		return "Printer is not paused\n"
	}

	printer.paused = false
	return "Machine is no longer paused\n"
}

var commandRegistry = map[string]func() Command{
	"G28": func() Command { return &G28Command{} },
	"G0":  func() Command { return &G0G1Command{} },
	"G1":  func() Command { return &G0G1Command{} },
	"M112": func() Command { return &CancelCommand{} },
	"M113": func() Command { return &KeepAliveCommand{state: true} },
	"M114":   func() Command { return &M114Command{} },
	"M997":   func() Command { return &M997Command{} },
	"M601":   func() Command { return &M601Command{} },
	"M602":   func() Command { return &M602Command{} },
}

func NewCommand(command string, printer *Printer) Command {
	for key, factory := range commandRegistry {
		if strings.HasPrefix(command, key) {
			if key == "G0" || key == "G1" {
				target, feedRate := parseMoveCommand(command, printer.extruder.Position)
				return &G0G1Command{target: target, feedRate: feedRate}
			}
			return factory()
		}
	}
	return nil
}

func parseMoveCommand(command string, currentPos Vector3) (Vector3, float64) {
	// Regular expression patterns for parsing
	reX := regexp.MustCompile(`X([-+]?[0-9]*\.?[0-9]+)`)
	reY := regexp.MustCompile(`Y([-+]?[0-9]*\.?[0-9]+)`)
	reZ := regexp.MustCompile(`Z([-+]?[0-9]*\.?[0-9]+)`)
	reF := regexp.MustCompile(`F([-+]?[0-9]*\.?[0-9]+)`)

	// Default target and feed rate
	target := currentPos
	feedRate := 3600.0 // Default feed rate

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
