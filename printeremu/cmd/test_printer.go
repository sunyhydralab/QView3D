package main

import (
	"fmt"
	"context"

	"printeremu/src"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
    defer cancel() 

	extruder, printer, err := src.Init(1, "Generic", "Marlin GCode", "EMU032uhb3293n2", "Testing Printer 1", "Init")

	if err != nil {
		fmt.Println(err)
		return
	}

	src.RunConnection(ctx, extruder, printer)
}