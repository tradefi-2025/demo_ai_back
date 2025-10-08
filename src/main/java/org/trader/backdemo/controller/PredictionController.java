package org.trader.backdemo.controller;


import lombok.AllArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.trader.backdemo.dto.request.PredictionRequest;
import org.trader.backdemo.dto.response.PredictionResponse;
import org.trader.backdemo.service.PredictionService;

import java.util.List;

@AllArgsConstructor
@RestController
@RequestMapping("/api/prediction")
public class PredictionController {

    private final PredictionService predictionService;

    @PostMapping("/predict")
    public ResponseEntity<PredictionResponse> predict(@RequestBody PredictionRequest predictionRequest) {

        return predictionService.predict(predictionRequest);
    }

    @GetMapping("/userPredictions")
    public ResponseEntity<List<PredictionResponse>> getUserPredictions(
            @AuthenticationPrincipal(expression = "id") Long userId) {
        return predictionService.getPredictionsByUser(userId);
    }
}
