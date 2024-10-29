package main

import (
	"fmt"

	"printeremu/src"
)

func main() {
	err := src.Init()

	if err != nil {
		fmt.Println(err)
	}

	src.Run()
}