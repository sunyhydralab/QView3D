package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"printeremu/src"
)

func main() {
	extruder, printer, err := src.Init(1, "Generic", "Marlin GCode", "EMU032uhb3293n2", "Testing Printer 1", "Init")

	if err != nil {
		fmt.Println("Error initializing printer:", err)
		return
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel() 

	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-signalChan
		cancel()
	}()

	go func() {
		src.RunConnection(ctx, extruder, printer)
	}()

	<-ctx.Done()
	log.Println("Shutting down...")
}