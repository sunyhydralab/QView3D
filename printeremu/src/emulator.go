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
    serverURL := "ws://127.0.0.1:8000"

    conn, _, err := websocket.DefaultDialer.Dial(serverURL, nil)

    if err != nil {
        log.Fatal("Failed to connect to server:", err)
    }

    defer conn.Close()

    fmt.Println("Connected to WebSocket server")

    RegisterPrinter(conn, printer)

    pingTicker := time.NewTicker(5 * time.Second)
    defer pingTicker.Stop()

    for {
        select {
        case <-ctx.Done():
            fmt.Println("Context canceled, closing connection.")
            return
        case <-pingTicker.C:
            pingMessage := map[string]interface{}{
                "event": "ping",
                "data":  "alive",
            }

            jsonPingMessage, err := json.Marshal(pingMessage)

            if err != nil {
                log.Println("Failed to marshal ping message:", err)
                return
            }

            if err := conn.WriteMessage(websocket.TextMessage, jsonPingMessage); err != nil {
                log.Println("Error sending ping message:", err)
                return
            }

        default:
            messageType, message, err := conn.ReadMessage()

            if err != nil {
                log.Println("Error reading message:", err)
                return
            }

            if messageType == websocket.TextMessage && string(message) == "close" {
                fmt.Println("Received 'close' signal from server, ending connection.")
                return
            }

            var parsedMessage map[string]interface{}

            if err := json.Unmarshal(message, &parsedMessage); err != nil {
                log.Println("Error parsing received message:", err)
                continue
            }

            event, ok := parsedMessage["event"].(string)

            if !ok {
                log.Println("Missing or invalid 'event' field:", parsedMessage)
                continue
            }

            data, _ := parsedMessage["data"]

            switch event {
            case "info":
                if message, exists := parsedMessage["message"].(string); exists {
                    log.Println("Info:", message)
                } else {
                    fmt.Println("Missing or invalid 'message' field in 'info' event data")
                }

            case "error":
                log.Println("Error:", data)

            default:
                log.Println("Received from server:", string(message))
            }
        }
    }
}

func RegisterPrinter(conn *websocket.Conn, printer *Printer) {
	message := map[string]interface{}{
		"event": "emuprintconnect",
		"data":  printer,
	}

	jsonMessage, err := json.Marshal(message)

	if err != nil {
		log.Println("Failed to marshal printer object:", err)
		return
	}

	log.Println("Registering printer...")

	conn.WriteMessage(websocket.TextMessage, []byte(jsonMessage))
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
