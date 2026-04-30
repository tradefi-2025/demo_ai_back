package org.trader.backdemo.controller;

import lombok.AllArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.trader.backdemo.dto.request.SignalStatusUpdateRequest;
import org.trader.backdemo.dto.response.SignalResponse;
import org.trader.backdemo.service.SignalService;

import java.util.List;

@AllArgsConstructor
@RestController
@RequestMapping("/api/signal")
public class SignalController {

    private final SignalService signalService;

    @GetMapping("/userSignals")
    public ResponseEntity<List<SignalResponse>> getUserSignals(
            @AuthenticationPrincipal(expression = "id") Long userId) {
        return signalService.getSignalsByUser(userId);
    }

    @PatchMapping("/{signalId}/status")
    public ResponseEntity<SignalResponse> updateSignalStatus(
            @PathVariable Long signalId,
            @AuthenticationPrincipal(expression = "id") Long userId,
            @RequestBody SignalStatusUpdateRequest request) {
        return signalService.updateSignalStatus(signalId, userId, request.getStatus());
    }

    @DeleteMapping("/{signalId}")
    public ResponseEntity<Void> deleteSignal(
            @PathVariable Long signalId,
            @AuthenticationPrincipal(expression = "id") Long userId) {
        return signalService.deleteSignal(signalId, userId);
    }
}
