package cashflow

import (
	"fmt"
	"sort"
	"time"
)

// Frequency represents the recurrence pattern for cashflow events
type Frequency string

const (
	Daily      Frequency = "daily"
	Weekly     Frequency = "weekly"
	Monthly    Frequency = "monthly"
	Quarterly  Frequency = "quarterly"
	SemiAnnual Frequency = "semi-annual"
	Annual     Frequency = "annual"
)

// Event represents a single cashflow event (income or expense)
type Event struct {
	Name      string    `json:"name"`
	StartDate time.Time `json:"start_date"`
	EndDate   time.Time `json:"end_date,omitempty"`
	Frequency Frequency `json:"frequency,omitempty"`
	Value     float64   `json:"value"`
	Obs       string    `json:"obs,omitempty"`
}

// CashflowItem represents a single cashflow entry for a specific date
type CashflowItem struct {
	Name  string  `json:"name"`
	Value float64 `json:"value"`
}

// Cashflow represents the aggregated cashflow for a specific date
type Cashflow struct {
	Date     time.Time      `json:"date"`
	Cashflow float64        `json:"cashflow"`
	Balance  float64        `json:"balance"`
	Items    []CashflowItem `json:"items"`
}

// SimulationRequest represents the input for a cashflow simulation
type SimulationRequest struct {
	Events         []Event   `json:"events"`
	InitialBalance float64   `json:"initial_balance"`
	SimStart       time.Time `json:"sim_start"`
	SimEnd         time.Time `json:"sim_end"`
}

// SimulationResponse represents the output of a cashflow simulation
type SimulationResponse struct {
	Cashflows []Cashflow `json:"cashflows"`
}

// frequencyDeltas maps frequencies to their time increments
var frequencyDeltas = map[Frequency]func(time.Time) time.Time{
	Daily:      func(t time.Time) time.Time { return t.AddDate(0, 0, 1) },
	Weekly:     func(t time.Time) time.Time { return t.AddDate(0, 0, 7) },
	Monthly:    func(t time.Time) time.Time { return t.AddDate(0, 1, 0) },
	Quarterly:  func(t time.Time) time.Time { return t.AddDate(0, 3, 0) },
	SemiAnnual: func(t time.Time) time.Time { return t.AddDate(0, 6, 0) },
	Annual:     func(t time.Time) time.Time { return t.AddDate(1, 0, 0) },
}

// IsValidFrequency checks if a frequency string is valid
func IsValidFrequency(freq Frequency) bool {
	_, ok := frequencyDeltas[freq]
	return ok
}

// GetNextDate calculates the next occurrence date based on frequency
func GetNextDate(currentDate time.Time, freq Frequency) (time.Time, error) {
	delta, ok := frequencyDeltas[freq]
	if !ok {
		return time.Time{}, fmt.Errorf("invalid frequency: %s", freq)
	}
	return delta(currentDate), nil
}

// GetFirstDate determines the first occurrence of an event within the cashflow period
func GetFirstDate(event Event, cfBegin, cfEnd time.Time) (time.Time, bool) {
	startDate := event.StartDate

	// Event starts after end of cashflow period
	if cfEnd.Before(startDate) {
		return time.Time{}, false
	}

	// Event ends before begin of cashflow period (if end date is set)
	if !event.EndDate.IsZero() && event.EndDate.Before(cfBegin) {
		return time.Time{}, false
	}

	// No frequency or start_date equals end_date
	if event.Frequency == "" || (!event.EndDate.IsZero() && startDate.Equal(event.EndDate)) {
		return startDate, true
	}

	// For daily events, return the begin of cashflow period
	if event.Frequency == Daily {
		return cfBegin, true
	}

	// Find first occurrence within the cashflow period
	currentDate := startDate
	for currentDate.Before(cfBegin) {
		nextDate, err := GetNextDate(currentDate, event.Frequency)
		if err != nil {
			return time.Time{}, false
		}
		currentDate = nextDate
	}

	return currentDate, true
}

// GenerateCashflows creates a list of cashflow events from input events
func GenerateCashflows(events []Event, cfBegin, cfEnd time.Time) ([]Cashflow, error) {
	if cfBegin.After(cfEnd) {
		return nil, fmt.Errorf("cf_begin must be before or equal to cf_end")
	}

	// Map to collect cashflows by date
	cfMap := make(map[time.Time][]CashflowItem)

	for _, event := range events {
		if event.Value == 0 {
			continue
		}

		currentDate, ok := GetFirstDate(event, cfBegin, cfEnd)
		if !ok {
			continue
		}

		for {
			// Check if we've exceeded the cashflow period
			if currentDate.After(cfEnd) {
				break
			}

			// Check if event has ended (if end date is set)
			if !event.EndDate.IsZero() && event.EndDate.Before(currentDate) {
				break
			}

			// Add to cashflow map
			item := CashflowItem{
				Name:  event.Name,
				Value: event.Value,
			}
			cfMap[currentDate] = append(cfMap[currentDate], item)

			// Get next date
			if event.Frequency == "" {
				break
			}

			nextDate, err := GetNextDate(currentDate, event.Frequency)
			if err != nil {
				break
			}
			currentDate = nextDate
		}
	}

	// Convert map to sorted slice
	cashflows := make([]Cashflow, 0, len(cfMap))
	for date, items := range cfMap {
		total := 0.0
		for _, item := range items {
			total += item.Value
		}
		cashflows = append(cashflows, Cashflow{
			Date:     date,
			Cashflow: total,
			Balance:  0, // Will be calculated later
			Items:    items,
		})
	}

	// Sort by date
	sortCashflowsByDate(cashflows)

	return cashflows, nil
}

// emptyCashflowItems is a shared empty slice to avoid allocation
var emptyCashflowItems = make([]CashflowItem, 0)

// BalanceFromCashflows calculates running balance from cashflows
func BalanceFromCashflows(initialBalance float64, simStart time.Time, cashflows []Cashflow) []Cashflow {
	result := make([]Cashflow, 0, len(cashflows)+1)

	// Add initial balance entry using shared empty slice
	result = append(result, Cashflow{
		Date:     simStart,
		Cashflow: 0,
		Balance:  initialBalance,
		Items:    emptyCashflowItems,
	})

	runningBalance := initialBalance
	for _, cf := range cashflows {
		runningBalance += cf.Cashflow
		cf.Balance = runningBalance
		result = append(result, cf)
	}

	return result
}

// sortCashflowsByDate sorts cashflows chronologically using introsort (O(n log n))
func sortCashflowsByDate(cashflows []Cashflow) {
	sort.Slice(cashflows, func(i, j int) bool {
		return cashflows[i].Date.Before(cashflows[j].Date)
	})
}

// RunSimulation executes a complete cashflow simulation
func RunSimulation(req SimulationRequest) (SimulationResponse, error) {
	cashflows, err := GenerateCashflows(req.Events, req.SimStart, req.SimEnd)
	if err != nil {
		return SimulationResponse{}, fmt.Errorf("failed to generate cashflows: %w", err)
	}

	result := BalanceFromCashflows(req.InitialBalance, req.SimStart, cashflows)

	return SimulationResponse{
		Cashflows: result,
	}, nil
}
