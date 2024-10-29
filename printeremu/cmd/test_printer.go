package main

import (
	"fmt"

	"printeremu/src"
)

func main() {
	extruder, printer, err := src.Init(1, "Ender3", "Creality", "hwid:032uhb3293n2", "Testing Printer", "Init")

	if err != nil {
		fmt.Println(err)
		return
	}

	src.Run(extruder, printer)
}