package src

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	socketio_client "github.com/zhouhui8915/go-socket.io-client"
)

type PrintJob struct {
	Command string
}

var jobQueue = make(chan PrintJob)

// Main function to initialize and run the printer emulator
func main() {
	extruder, printer, err := Init(1, "Device1", "Test Printer", "HWID1234", "Printer1", "Active")
	if err != nil {
		log.Fatalf("Failed to initialize printer: %v", err)
	}
	RunCommand(extruder, printer)
}

// Init function initializes the Extruder and Printer
func Init(id int, device string, description string, hwid string, name string, status string) (*Extruder, *Printer, error) {
	fmt.Println("Initializing printer...")

	position := Vector3{X: 100, Y: 27, Z: 76}
	extruder := NewExtruder(position, 250, 100, 125)

	// Create a new heatbed instance
	heatbed := &Heatbed{
		Temp:       60.0,  // Default initial temperature
		TargetTemp: 100.0, // Target temperature for the heatbed
	}

	printer := NewPrinter(id, device, description, hwid, name, status, time.Now().String(), extruder, heatbed)

	fmt.Println(printer.String())

	return extruder, printer, nil
}

func RunConnection(ctx context.Context, extruder *Extruder, printer *Printer) {
	opts := &socketio_client.Options{
		Transport: "websocket",
	}

	uri := "http://127.0.0.1:8000/"
	c, err := socketio_client.NewClient(uri, opts)
	if err != nil {
		log.Printf("NewClient error: %v\n", err)
		return
	}

	log.Println("Attempting to connect...")

	if c == nil {
		log.Println("Failed to create socket.io client.")
		return
	}

	c.On("connection", func() {
		log.Println("Connected to backend with virtual USB...")
		RegisterPrinter(c, printer)
	})

	c.On("disconnection", func() {
		log.Println("Disconnected from backend")
	})

	c.On("error", func(err error) {
		log.Println("Socket error:", err)
	})

	go ProcessJobs(ctx, printer, c)

	select {
	case <-ctx.Done():
		log.Println("Stopping connection...")
	}
}

func RegisterPrinter(c *socketio_client.Client, printer *Printer) {
	jsonPrinter, err := json.Marshal(printer)
	if err != nil {
		log.Println("Failed to marshal printer object:", err)
		return
	}

	log.Println("Emitting emuprintconnect event with data:", string(jsonPrinter))
	c.Emit("emuprintconnect", jsonPrinter)
}

func ProcessJobs(ctx context.Context, printer *Printer, c *socketio_client.Client) {
	for {
		select {
		case job := <-jobQueue:
			response := CommandHandler(job.Command, printer)

			// todo: handle weird edge case responses
			/* 		if job.Command == "G29" {

			} else if job.Command == "G92" {

			}
			*/
			if !strings.Contains(response, "Unknown command") {
				c.Emit("job_response", "ok\n")
			}
		case <-ctx.Done():
			log.Println("Stopping job processing...")
			return
		}
	}
}

// Run function for G-code command input and processing
func RunCommand(extruder *Extruder, printer *Printer) {
	scanner := bufio.NewScanner(os.Stdin)

	fmt.Println("Enter G-code commands (type 'exit' or 'quit' to quit):")

	for {
		fmt.Print("> ")
		scanner.Scan()
		command := scanner.Text()

		if strings.ToLower(command) == "exit" || strings.ToLower(command) == "quit" {
			fmt.Println("Exiting printer emulator...")
			break
		}

		response := CommandHandler(command, printer)
		fmt.Println(response)
	}

	if err := scanner.Err(); err != nil {
		log.Println("Error reading input:", err)
	}
}
