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

	"github.com/gorilla/websocket"
)

type Event struct {
	Event string      `json:"event"`
	Data  interface{} `json:"data"`
}

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
	// Connect to the WebSocket server
	serverURL := "ws://127.0.0.1:8000"
	conn, _, err := websocket.DefaultDialer.Dial(serverURL, nil)
	if err != nil {
		log.Fatal("Failed to connect to server:", err)
	}
	defer conn.Close()

	fmt.Println("Connected to WebSocket server")

	// Send a message to the server
	err = conn.WriteMessage(websocket.TextMessage, []byte("Hello from Go client!"))
	if err != nil {
		log.Fatal("Failed to send message:", err)
	}

	// Read the server's response
	_, message, err := conn.ReadMessage()
	if err != nil {
		log.Fatal("Failed to read message:", err)
	}

	fmt.Println("Received from server:", string(message))

	// Keep the connection alive
	time.Sleep(5 * time.Second)
}

func RegisterPrinter(c *SocketIOClient, printer *Printer) {
	jsonPrinter, err := json.Marshal(printer)
	if err != nil {
		log.Println("Failed to marshal printer object:", err)
		return
	}

	log.Println("Emitting emuprintconnect event with JSON data:", string(jsonPrinter))
	//c.Emit("emuprintconnect", string(jsonPrinter))
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
