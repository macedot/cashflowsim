package cashflow

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
)

// Server represents the HTTP API server
type Server struct {
	port   string
	logger *log.Logger
}

// NewServer creates a new API server instance
func NewServer(port string, logger *log.Logger) *Server {
	if logger == nil {
		logger = log.Default()
	}
	return &Server{
		port:   port,
		logger: logger,
	}
}

// healthResponse represents the health check response
type healthResponse struct {
	Status    string    `json:"status"`
	Timestamp time.Time `json:"timestamp"`
}

// simulateRequest represents the simulation API request
type simulateRequest struct {
	Events         []Event   `json:"events"`
	InitialBalance float64   `json:"initial_balance"`
	SimStart       time.Time `json:"sim_start"`
	SimEnd         time.Time `json:"sim_end"`
}

// simulateResponse represents the simulation API response
type simulateResponse struct {
	Cashflows []Cashflow `json:"cashflows"`
}

// errorResponse represents an API error response
type errorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message,omitempty"`
}

// writeJSON writes a JSON response with the given status code
func writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(data); err != nil {
		log.Printf("Failed to encode JSON response: %v", err)
	}
}

// writeError writes an error response
func writeError(w http.ResponseWriter, status int, err string, message string) {
	writeJSON(w, status, errorResponse{Error: err, Message: message})
}

// loggingMiddleware wraps an HTTP handler with logging
func (s *Server) loggingMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next(w, r)
		s.logger.Printf("%s %s %s %v", r.Method, r.URL.Path, r.RemoteAddr, time.Since(start))
	}
}

// recoveryMiddleware recovers from panics
func (s *Server) recoveryMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				s.logger.Printf("Panic recovered: %v", err)
				writeError(w, http.StatusInternalServerError, "internal_error", "An unexpected error occurred")
			}
		}()
		next(w, r)
	}
}

// handleHealth handles the health check endpoint
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "method_not_allowed", "Only GET method is allowed")
		return
	}

	writeJSON(w, http.StatusOK, healthResponse{
		Status:    "ok",
		Timestamp: time.Now().UTC(),
	})
}

// handleSimulate handles the simulation endpoint
func (s *Server) handleSimulate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "method_not_allowed", "Only POST method is allowed")
		return
	}

	var req simulateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", fmt.Sprintf("Failed to parse request body: %v", err))
		return
	}

	// Validate request
	if req.SimStart.IsZero() || req.SimEnd.IsZero() {
		writeError(w, http.StatusBadRequest, "missing_dates", "sim_start and sim_end are required")
		return
	}

	if req.SimStart.After(req.SimEnd) {
		writeError(w, http.StatusBadRequest, "invalid_range", "sim_start must be before sim_end")
		return
	}

	// Run simulation
	simReq := SimulationRequest{
		Events:         req.Events,
		InitialBalance: req.InitialBalance,
		SimStart:       req.SimStart,
		SimEnd:         req.SimEnd,
	}

	resp, err := RunSimulation(simReq)
	if err != nil {
		s.logger.Printf("Simulation error: %v", err)
		writeError(w, http.StatusInternalServerError, "simulation_failed", err.Error())
		return
	}

	writeJSON(w, http.StatusOK, resp)
}

// SetupRoutes configures all HTTP routes
func (s *Server) SetupRoutes() {
	// Health endpoint
	http.HandleFunc("/health", s.recoveryMiddleware(s.loggingMiddleware(s.handleHealth)))

	// Simulation endpoint (versioned)
	http.HandleFunc("/api/v1/simulate", s.recoveryMiddleware(s.loggingMiddleware(s.handleSimulate)))

	// Root handler for 404s
	http.HandleFunc("/", s.recoveryMiddleware(s.loggingMiddleware(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			writeError(w, http.StatusNotFound, "not_found", fmt.Sprintf("Endpoint %s not found", r.URL.Path))
			return
		}
		writeJSON(w, http.StatusOK, map[string]string{
			"service": "cashflowsim",
			"version": "1.0.0",
			"status":  "running",
		})
	})))
}

// Start begins listening for HTTP requests
func (s *Server) Start() error {
	s.SetupRoutes()
	s.logger.Printf("Starting server on port %s", s.port)
	return http.ListenAndServe(":"+s.port, nil)
}
