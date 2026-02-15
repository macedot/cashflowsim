package cashflow

import (
	"testing"
	"time"
)

func TestIsValidFrequency(t *testing.T) {
	tests := []struct {
		name     string
		freq     Frequency
		expected bool
	}{
		{"daily is valid", Daily, true},
		{"weekly is valid", Weekly, true},
		{"monthly is valid", Monthly, true},
		{"quarterly is valid", Quarterly, true},
		{"semi-annual is valid", SemiAnnual, true},
		{"annual is valid", Annual, true},
		{"invalid frequency", "invalid", false},
		{"empty frequency", "", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsValidFrequency(tt.freq)
			if result != tt.expected {
				t.Errorf("IsValidFrequency(%q) = %v, want %v", tt.freq, result, tt.expected)
			}
		})
	}
}

func TestGetNextDate(t *testing.T) {
	baseDate := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)

	tests := []struct {
		name     string
		freq     Frequency
		expected time.Time
	}{
		{"daily adds 1 day", Daily, time.Date(2025, 1, 2, 0, 0, 0, 0, time.UTC)},
		{"weekly adds 7 days", Weekly, time.Date(2025, 1, 8, 0, 0, 0, 0, time.UTC)},
		{"monthly adds 1 month", Monthly, time.Date(2025, 2, 1, 0, 0, 0, 0, time.UTC)},
		{"quarterly adds 3 months", Quarterly, time.Date(2025, 4, 1, 0, 0, 0, 0, time.UTC)},
		{"semi-annual adds 6 months", SemiAnnual, time.Date(2025, 7, 1, 0, 0, 0, 0, time.UTC)},
		{"annual adds 1 year", Annual, time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := GetNextDate(baseDate, tt.freq)
			if err != nil {
				t.Fatalf("GetNextDate() error = %v", err)
			}
			if !result.Equal(tt.expected) {
				t.Errorf("GetNextDate() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestGetNextDate_InvalidFrequency(t *testing.T) {
	baseDate := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	_, err := GetNextDate(baseDate, "invalid")
	if err == nil {
		t.Error("GetNextDate() with invalid frequency should return error")
	}
}

func TestGetFirstDate(t *testing.T) {
	cfBegin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2025, 12, 31, 0, 0, 0, 0, time.UTC)

	tests := []struct {
		name         string
		event        Event
		expectedDate time.Time
		expectedOk   bool
	}{
		{
			name: "event within period",
			event: Event{
				StartDate: time.Date(2025, 6, 1, 0, 0, 0, 0, time.UTC),
				Value:     100,
			},
			expectedDate: time.Date(2025, 6, 1, 0, 0, 0, 0, time.UTC),
			expectedOk:   true,
		},
		{
			name: "event starts after period",
			event: Event{
				StartDate: time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC),
				Value:     100,
			},
			expectedOk: false,
		},
		{
			name: "event ends before period",
			event: Event{
				StartDate: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
				EndDate:   time.Date(2024, 12, 31, 0, 0, 0, 0, time.UTC),
				Value:     100,
			},
			expectedOk: false,
		},
		{
			name: "daily event returns cf_begin",
			event: Event{
				StartDate: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
				Frequency: Daily,
				Value:     100,
			},
			expectedDate: cfBegin,
			expectedOk:   true,
		},
		{
			name: "monthly event finds first occurrence",
			event: Event{
				StartDate: time.Date(2024, 6, 15, 0, 0, 0, 0, time.UTC),
				Frequency: Monthly,
				Value:     100,
			},
			expectedDate: time.Date(2025, 1, 15, 0, 0, 0, 0, time.UTC),
			expectedOk:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, ok := GetFirstDate(tt.event, cfBegin, cfEnd)
			if ok != tt.expectedOk {
				t.Errorf("GetFirstDate() ok = %v, want %v", ok, tt.expectedOk)
			}
			if ok && !result.Equal(tt.expectedDate) {
				t.Errorf("GetFirstDate() date = %v, want %v", result, tt.expectedDate)
			}
		})
	}
}

func TestGenerateCashflows(t *testing.T) {
	cfBegin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2025, 3, 31, 0, 0, 0, 0, time.UTC)

	tests := []struct {
		name          string
		events        []Event
		expectedLen   int
		expectedTotal float64
	}{
		{
			name: "single one-time event",
			events: []Event{
				{StartDate: time.Date(2025, 1, 15, 0, 0, 0, 0, time.UTC), Value: 1000},
			},
			expectedLen:   1,
			expectedTotal: 1000,
		},
		{
			name: "monthly salary",
			events: []Event{
				{
					StartDate: time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC),
					Frequency: Monthly,
					Value:     5000,
				},
			},
			expectedLen:   3, // Jan, Feb, Mar
			expectedTotal: 15000,
		},
		{
			name: "event with zero value is skipped",
			events: []Event{
				{StartDate: time.Date(2025, 1, 15, 0, 0, 0, 0, time.UTC), Value: 0},
			},
			expectedLen:   0,
			expectedTotal: 0,
		},
		{
			name: "multiple events on same date",
			events: []Event{
				{StartDate: time.Date(2025, 1, 15, 0, 0, 0, 0, time.UTC), Value: 1000},
				{StartDate: time.Date(2025, 1, 15, 0, 0, 0, 0, time.UTC), Value: 2000},
			},
			expectedLen:   1,
			expectedTotal: 3000,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cashflows, err := GenerateCashflows(tt.events, cfBegin, cfEnd)
			if err != nil {
				t.Fatalf("GenerateCashflows() error = %v", err)
			}
			if len(cashflows) != tt.expectedLen {
				t.Errorf("GenerateCashflows() len = %v, want %v", len(cashflows), tt.expectedLen)
			}

			total := 0.0
			for _, cf := range cashflows {
				total += cf.Cashflow
			}
			if total != tt.expectedTotal {
				t.Errorf("Total cashflow = %v, want %v", total, tt.expectedTotal)
			}
		})
	}
}

func TestGenerateCashflows_InvalidRange(t *testing.T) {
	cfBegin := time.Date(2025, 12, 31, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)

	_, err := GenerateCashflows([]Event{}, cfBegin, cfEnd)
	if err == nil {
		t.Error("GenerateCashflows() with invalid range should return error")
	}
}

func TestBalanceFromCashflows(t *testing.T) {
	simStart := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cashflows := []Cashflow{
		{Date: time.Date(2025, 1, 15, 0, 0, 0, 0, time.UTC), Cashflow: 1000},
		{Date: time.Date(2025, 2, 15, 0, 0, 0, 0, time.UTC), Cashflow: 2000},
		{Date: time.Date(2025, 3, 15, 0, 0, 0, 0, time.UTC), Cashflow: -500},
	}

	result := BalanceFromCashflows(5000, simStart, cashflows)

	if len(result) != 4 { // initial + 3 cashflows
		t.Errorf("BalanceFromCashflows() len = %v, want 4", len(result))
	}

	// Check initial balance
	if result[0].Balance != 5000 {
		t.Errorf("Initial balance = %v, want 5000", result[0].Balance)
	}

	// Check running balances
	expectedBalances := []float64{5000, 6000, 8000, 7500}
	for i, expected := range expectedBalances {
		if result[i].Balance != expected {
			t.Errorf("Balance[%d] = %v, want %v", i, result[i].Balance, expected)
		}
	}
}

func TestRunSimulation(t *testing.T) {
	req := SimulationRequest{
		Events: []Event{
			{
				Name:      "Salary",
				StartDate: time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC),
				Frequency: Monthly,
				Value:     5000,
			},
			{
				Name:      "Rent",
				StartDate: time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC),
				Frequency: Monthly,
				Value:     -1500,
			},
		},
		InitialBalance: 1000,
		SimStart:       time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC),
		SimEnd:         time.Date(2025, 3, 31, 0, 0, 0, 0, time.UTC),
	}

	resp, err := RunSimulation(req)
	if err != nil {
		t.Fatalf("RunSimulation() error = %v", err)
	}

	// Should have initial + 3 months
	if len(resp.Cashflows) != 4 {
		t.Errorf("RunSimulation() cashflows len = %v, want 4", len(resp.Cashflows))
	}

	// Check final balance: 1000 + (5000-1500)*3 = 1000 + 10500 = 11500
	finalBalance := resp.Cashflows[len(resp.Cashflows)-1].Balance
	if finalBalance != 11500 {
		t.Errorf("Final balance = %v, want 11500", finalBalance)
	}
}

func TestSortCashflowsByDate(t *testing.T) {
	cashflows := []Cashflow{
		{Date: time.Date(2025, 3, 1, 0, 0, 0, 0, time.UTC), Cashflow: 300},
		{Date: time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC), Cashflow: 100},
		{Date: time.Date(2025, 2, 1, 0, 0, 0, 0, time.UTC), Cashflow: 200},
	}

	sortCashflowsByDate(cashflows)

	expectedOrder := []int{100, 200, 300}
	for i, expected := range expectedOrder {
		if cashflows[i].Cashflow != float64(expected) {
			t.Errorf("After sort, cashflows[%d].Cashflow = %v, want %v", i, cashflows[i].Cashflow, expected)
		}
	}
}

func TestGenerateCashflows_WithEndDate(t *testing.T) {
	cfBegin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2025, 12, 31, 0, 0, 0, 0, time.UTC)

	events := []Event{
		{
			Name:      "Contract",
			StartDate: time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC),
			EndDate:   time.Date(2025, 3, 31, 0, 0, 0, 0, time.UTC),
			Frequency: Monthly,
			Value:     1000,
		},
	}

	cashflows, err := GenerateCashflows(events, cfBegin, cfEnd)
	if err != nil {
		t.Fatalf("GenerateCashflows() error = %v", err)
	}

	if len(cashflows) != 3 {
		t.Errorf("Expected 3 cashflows (Jan, Feb, Mar), got %d", len(cashflows))
	}
}

func TestGenerateCashflows_NegativeValues(t *testing.T) {
	cfBegin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2025, 1, 31, 0, 0, 0, 0, time.UTC)

	events := []Event{
		{
			Name:      "Expense",
			StartDate: time.Date(2025, 1, 15, 0, 0, 0, 0, time.UTC),
			Value:     -500,
		},
		{
			Name:      "Income",
			StartDate: time.Date(2025, 1, 10, 0, 0, 0, 0, time.UTC),
			Value:     2000,
		},
	}

	cashflows, err := GenerateCashflows(events, cfBegin, cfEnd)
	if err != nil {
		t.Fatalf("GenerateCashflows() error = %v", err)
	}

	if len(cashflows) != 2 {
		t.Errorf("Expected 2 cashflow entries, got %d", len(cashflows))
	}

	total := 0.0
	for _, cf := range cashflows {
		total += cf.Cashflow
	}
	if total != 1500 {
		t.Errorf("Total cashflow = %v, want 1500", total)
	}
}

func TestGenerateCashflows_EmptyEvents(t *testing.T) {
	cfBegin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2025, 12, 31, 0, 0, 0, 0, time.UTC)

	cashflows, err := GenerateCashflows([]Event{}, cfBegin, cfEnd)
	if err != nil {
		t.Fatalf("GenerateCashflows() error = %v", err)
	}

	if len(cashflows) != 0 {
		t.Errorf("Expected 0 cashflows for empty events, got %d", len(cashflows))
	}
}

func TestBalanceFromCashflows_EmptyCashflows(t *testing.T) {
	simStart := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)

	result := BalanceFromCashflows(1000, simStart, []Cashflow{})

	if len(result) != 1 {
		t.Errorf("Expected 1 entry (initial balance), got %d", len(result))
	}
	if result[0].Balance != 1000 {
		t.Errorf("Initial balance = %v, want 1000", result[0].Balance)
	}
}

func TestGetFirstDate_EventStartsAtCFEnd(t *testing.T) {
	cfBegin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2025, 12, 31, 0, 0, 0, 0, time.UTC)

	event := Event{
		StartDate: cfEnd,
		Value:     100,
	}

	date, ok := GetFirstDate(event, cfBegin, cfEnd)
	if !ok {
		t.Error("Expected to find first date at cfEnd")
	}
	if !date.Equal(cfEnd) {
		t.Errorf("Expected date = %v, got %v", cfEnd, date)
	}
}

func TestGenerateCashflows_AnnualFrequency(t *testing.T) {
	cfBegin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2027, 12, 31, 0, 0, 0, 0, time.UTC)

	events := []Event{
		{
			Name:      "Yearly Bonus",
			StartDate: time.Date(2025, 6, 1, 0, 0, 0, 0, time.UTC),
			Frequency: Annual,
			Value:     12000,
		},
	}

	cashflows, err := GenerateCashflows(events, cfBegin, cfEnd)
	if err != nil {
		t.Fatalf("GenerateCashflows() error = %v", err)
	}

	if len(cashflows) != 3 {
		t.Errorf("Expected 3 occurrences (2025, 2026, 2027), got %d", len(cashflows))
	}

	total := 0.0
	for _, cf := range cashflows {
		total += cf.Cashflow
	}
	if total != 36000 {
		t.Errorf("Total = %v, want 36000", total)
	}
}

func TestGenerateCashflows_QuarterlyFrequency(t *testing.T) {
	cfBegin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2025, 12, 31, 0, 0, 0, 0, time.UTC)

	events := []Event{
		{
			Name:      "Quarterly Payment",
			StartDate: time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC),
			Frequency: Quarterly,
			Value:     3000,
		},
	}

	cashflows, err := GenerateCashflows(events, cfBegin, cfEnd)
	if err != nil {
		t.Fatalf("GenerateCashflows() error = %v", err)
	}

	if len(cashflows) != 4 {
		t.Errorf("Expected 4 quarters, got %d", len(cashflows))
	}
}

func TestGetFirstDate_NoFrequencyOneTime(t *testing.T) {
	cfBegin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2025, 12, 31, 0, 0, 0, 0, time.UTC)

	event := Event{
		StartDate: time.Date(2025, 6, 15, 0, 0, 0, 0, time.UTC),
		Frequency: "",
		Value:     100,
	}

	date, ok := GetFirstDate(event, cfBegin, cfEnd)
	if !ok {
		t.Error("Expected ok=true for one-time event")
	}
	if !date.Equal(event.StartDate) {
		t.Errorf("Expected date = %v, got %v", event.StartDate, date)
	}
}

func TestGetFirstDate_StartEqualsEnd(t *testing.T) {
	cfBegin := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	cfEnd := time.Date(2025, 12, 31, 0, 0, 0, 0, time.UTC)

	event := Event{
		StartDate: time.Date(2025, 6, 15, 0, 0, 0, 0, time.UTC),
		EndDate:   time.Date(2025, 6, 15, 0, 0, 0, 0, time.UTC),
		Frequency: Monthly,
		Value:     100,
	}

	date, ok := GetFirstDate(event, cfBegin, cfEnd)
	if !ok {
		t.Error("Expected ok=true when start equals end")
	}
	if !date.Equal(event.StartDate) {
		t.Errorf("Expected date = %v, got %v", event.StartDate, date)
	}
}
