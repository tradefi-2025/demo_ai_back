package org.trader.backdemo.service;

import lombok.AllArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import org.trader.backdemo.dto.external.ExternalPredictionRequest;
import org.trader.backdemo.dto.external.ExternalPredictionResponse;
import org.trader.backdemo.dto.request.PredictionRequest;
import org.trader.backdemo.dto.response.PredictionResponse;
import org.trader.backdemo.entity.AgentEntity;
import org.trader.backdemo.entity.PredictionEntity;
import org.trader.backdemo.repository.AgentRepository;
import org.trader.backdemo.repository.PredictionRepository;
import org.trader.backdemo.service.client.PredictionFeignClient;

import java.util.List;

@AllArgsConstructor
@Service
public class PredictionService {

    private final PredictionFeignClient predictionFeignClient;
    private final AgentRepository agentRepository;
    private final PredictionRepository predictionRepository;

    public ResponseEntity<PredictionResponse> predict(PredictionRequest predictionRequest) {

        ExternalPredictionRequest body = new ExternalPredictionRequest(
                predictionRequest.getAgentId(),
                predictionRequest.getPredictionDate()
        );

        ResponseEntity<ExternalPredictionResponse> predictionResult = predictionFeignClient.predictExternal(body);
        if (!predictionResult.getStatusCode().is2xxSuccessful())
            throw new ResponseStatusException(predictionResult.getStatusCode(), "Error from prediction service");

        if (!predictionResult.hasBody()) {
            throw new ResponseStatusException(predictionResult.getStatusCode(), "the body is null");
        }
        ExternalPredictionResponse externalResponse = predictionResult.getBody();

        PredictionEntity predictionEntity = new PredictionEntity();

        AgentEntity agentEntity = agentRepository.findById(predictionRequest.getAgentId())
                .orElseThrow(() -> new ResponseStatusException(org.springframework.http.HttpStatus.NOT_FOUND, "Agent not found"));
        predictionEntity.setAgent(agentEntity);
        predictionEntity.setPredictionDate(predictionRequest.getPredictionDate());
        if (externalResponse.getPrediction() != null) {
            predictionEntity.setPredictedData(externalResponse.getPrediction());
        }
        if (externalResponse.getActualMarket() != null) {
            predictionEntity.setActualMarket(externalResponse.getActualMarket());
        }

        long predictionId = predictionRepository.save(predictionEntity).getId();

        return ResponseEntity.ok(PredictionResponse.builder()
                .predictionId(predictionId)
                .agentId(agentEntity.getId())
                .targetMarket(agentEntity.getTargetMarket())
                .predictionDate(predictionRequest.getPredictionDate())
                .prediction(externalResponse.getPrediction())
                .actualMarket(externalResponse.getActualMarket())
                .build());


    }


    public ResponseEntity<List<PredictionResponse>> getPredictionsByUser(Long userId) {
        // Récupérer tous les agents de l'utilisateur
        List<AgentEntity> userAgents = agentRepository.findByUserId(userId);

        if (userAgents.isEmpty()) {
            return ResponseEntity.ok(List.of());
        }

        // Récupérer les IDs des agents
        List<Long> agentIds = userAgents.stream().map(AgentEntity::getId).toList();

        // Récupérer toutes les prédictions de ces agents
        List<PredictionEntity> predictions = predictionRepository.findByAgentIdIn(agentIds);

        // Convertir en DTO avec toutes les infos nécessaires
        List<PredictionResponse> response = predictions.stream()
                .map(p -> PredictionResponse.builder()
                        .predictionId(p.getId())
                        .agentId(p.getAgent().getId())
                        .targetMarket(p.getAgent().getTargetMarket())
                        .predictionDate(p.getPredictionDate())
                        .prediction(p.getPredictedData())
                        .actualMarket(p.getActualMarket())
                        .build())
                .toList();

        return ResponseEntity.ok(response);
    }
}
