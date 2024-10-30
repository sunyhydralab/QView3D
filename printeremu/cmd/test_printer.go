package main

import (
	"fmt"

	"printeremu/src"
)

func main() {
	extruder, printer, err := src.Init(1, "Generic", "Marlin GCode", "hwid:032uhb3293n2", "Testing Printer 1", "Init")

	if err != nil {
		fmt.Println(err)
		return
	}

	src.Run(extruder, printer)
}