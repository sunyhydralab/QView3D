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
	client := NewClient()
	defer client.Close()

	client.On("connection", func(data interface{}) {
		fmt.Println("Connected to backend!")

		RegisterPrinter(client, printer)
	})

	client.On("disconnect", func(data interface{}) {
		log.Println("Disconnected from backend")
		close(jobQueue)
	})
	
	client.On("error", func(data interface{}) {
		if err, ok := data.(error); ok {
			log.Println("Socket error:", err)
		}
	})

    log.Println("Attempting to connect...")
    err := client.Connect("http://127.0.0.1:8000")
    if err != nil {
        log.Printf("Connection error: %v\n", err)
        return
    }

    go ProcessJobs(ctx, printer, client)

	<-ctx.Done()
	log.Println("Connection stopping...")
}

func RegisterPrinter(c *SocketIOClient, printer *Printer) {
	jsonPrinter, err := json.Marshal(printer)

	if err != nil {
		log.Println("Failed to marshal printer object:", err)
		return
	}

	log.Println("Emitting emuprintconnect event with data:", string(jsonPrinter))
	c.Emit("emuprintconnect", jsonPrinter)
}

func ProcessJobs(ctx context.Context, printer *Printer, c *SocketIOClient) {
	for {
		select {
		case job, ok := <-jobQueue:
			if !ok {
				log.Println("Job queue closed, exiting ProcessJobs.")
				return
			}

			response := CommandHandler(job.Command, printer)
			log.Printf("Processing job: %s, response: %s\n", job.Command, response)

			// todo: handle weird edge case responses
			/* 		if job.Command == "G29" {

			} else if job.Command == "G92" {

			}
			*/
			if !strings.Contains(response, "Unknown command") {
				c.Emit("job_response", "ok\n")
			}
		case <-c.close:
			log.Println("Client connection closed.")
			return
		case <-ctx.Done():
			log.Println("Context done, exiting ProcessJobs.")
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
