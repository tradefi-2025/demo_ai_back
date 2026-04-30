package org.trader.backdemo.service;

import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import org.trader.backdemo.dto.response.SignalProbabilitiesResponse;
import org.trader.backdemo.dto.response.SignalResponse;
import org.trader.backdemo.entity.SignalEntity;
import org.trader.backdemo.entity.SignalProbabilities;
import org.trader.backdemo.repository.SignalRepository;

import java.util.List;

@AllArgsConstructor
@Service
public class SignalService {

    private final SignalRepository signalRepository;

    public ResponseEntity<List<SignalResponse>> getSignalsByUser(Long userId) {
        List<SignalResponse> response = signalRepository.findByAgentUserIdOrderBySignalDateDesc(userId).stream()
                .map(this::toResponse)
                .toList();
        return ResponseEntity.ok(response);
    }

    public ResponseEntity<SignalResponse> updateSignalStatus(Long signalId,
                                                             Long userId,
                                                             SignalEntity.SignalStatus status) {
        if (status == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Signal status is required");
        }

        SignalEntity signal = signalRepository.findByIdAndAgentUserId(signalId, userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Signal not found"));

        signal.setStatus(status);
        SignalEntity updatedSignal = signalRepository.save(signal);
        return ResponseEntity.ok(toResponse(updatedSignal));
    }

    public ResponseEntity<Void> deleteSignal(Long signalId, Long userId) {
        SignalEntity signal = signalRepository.findByIdAndAgentUserId(signalId, userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Signal not found"));
        signalRepository.delete(signal);
        return ResponseEntity.noContent().build();
    }

    private SignalResponse toResponse(SignalEntity signal) {
        return SignalResponse.builder()
                .signalId(signal.getId())
                .agentId(signal.getAgent().getId())
                .agentName(signal.getAgent().getName())
                .signalDate(signal.getSignalDate())
                .estimatedAction(signal.getEstimatedAction())
                .signal(signal.getSignal())
                .probability(signal.getProbability())
                .probabilities(toProbabilitiesResponse(signal.getProbabilities()))
                .volume(signal.getVolume())
                .notional(signal.getNotional())
                .stopLossPrice(signal.getStopLossPrice())
                .riskAmount(signal.getRiskAmount())
                .sizingMethod(signal.getSizingMethod())
                .warnings(signal.getWarnings())
                .status(signal.getStatus())
                .build();
    }

    private SignalProbabilitiesResponse toProbabilitiesResponse(SignalProbabilities probabilities) {
        if (probabilities == null) {
            return null;
        }
        return SignalProbabilitiesResponse.builder()
                .sell(probabilities.getSell())
                .hold(probabilities.getHold())
                .buy(probabilities.getBuy())
                .build();
    }
}
