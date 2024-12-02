package src

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"time"

	"golang.org/x/exp/rand"
)

type PrinterConfig struct {
	Id         int                    `json:"id"`
	Name       string                 `json:"name"`
	Brand      PrinterBrand           `json:"brand"`
	Data       map[string]interface{} `json:"data"`
	Attributes map[string]interface{} `json:"attributes"`
}

type PrinterBrand struct {
	PrinterName  string `json:"printerName"`
	PrinterModel string `json:"printerModel"`
}

// LoadPrinters loads a list of printers from the specified JSON file
func LoadPrinters(filePath string) ([]Printer, error) {
	file, err := os.Open(filePath)

	if err != nil {
		return nil, fmt.Errorf("failed to open file %s: %v", filePath, err)
	}

	defer file.Close()

	fileBytes, err := io.ReadAll(file)

	if err != nil {
		return nil, fmt.Errorf("failed to read file: %v", err)
	}

	var printersConfig []PrinterConfig
	err = json.Unmarshal(fileBytes, &printersConfig)

	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal JSON data: %v", err)
	}

	var printers []Printer

	for _, printerConfig := range printersConfig {
		_, printer, err := Init(printerConfig.Id, printerConfig.Brand.PrinterName+" "+printerConfig.Brand.PrinterModel, "Marlin GCode", "EMU-"+RandomString(8), printerConfig.Name, "Init")

		// always add the model as an attribute so we always know what the model is
		printer.AddAttribute("model", printerConfig.Brand.PrinterName)

		for key, value := range printerConfig.Attributes {
			printer.AddAttribute(key, value)
		}

		for key, value := range printerConfig.Data {
			printer.AddData(key, value)
		}

		if err != nil {
			return nil, fmt.Errorf("failed to initialize printer %d: %v", printerConfig.Id, err)
		}

		PostRegistry(printer)

		printers = append(printers, *printer)
	}

	return printers, nil
}

func PrintPrinters(printers []Printer) {
	fmt.Println("Loaded printers:")

	for _, printer := range printers {
		fmt.Println(printer.String())
	}
}

func GetPrinter(id int, printers []Printer) *Printer {
	for _, printer := range printers {
		if printer.Id == id {
			return &printer
		}
	}

	return nil
}

func RandomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	rand.Seed(uint64(time.Now().UnixNano()))

	var result []byte

	for i := 0; i < length; i++ {
		result = append(result, charset[rand.Intn(len(charset))])
	}

	return string(result)
}