package src

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type EmulatorSettings struct {
	EnabledPrinters []string `json:"enabledPrinters"`
	DefaultAddress  string   `json:"defaultAddress"`
	DefaultPort     int      `json:"defaultPort"`
	Startup         string   `json:"startup"`
}

func LoadSettings(filePath string) (EmulatorSettings, error) {
	file, err := os.Open(filePath)

	if err != nil {
		return EmulatorSettings{}, fmt.Errorf("failed to open file %s: %v", filePath, err)
	}

	defer file.Close()

	fileBytes, err := io.ReadAll(file)

	if err != nil {
		return EmulatorSettings{}, fmt.Errorf("failed to read file: %v", err)
	}

	var settings EmulatorSettings
	err = json.Unmarshal(fileBytes, &settings)

	if err != nil {
		return EmulatorSettings{}, fmt.Errorf("failed to unmarshal JSON data: %v", err)
	}

	return settings, nil
}
