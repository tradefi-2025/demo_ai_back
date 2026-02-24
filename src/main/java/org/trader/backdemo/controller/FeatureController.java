package org.trader.backdemo.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.trader.backdemo.dto.request.FeatureCreateRequest;
import org.trader.backdemo.service.FeatureService;
import org.trader.backdemo.dto.response.*;

@RestController
@RequestMapping("/api/feature")
public class FeatureController {

    private final FeatureService featureService;


    public FeatureController(FeatureService featureService) {
        this.featureService = featureService;
    }

    @GetMapping("/getAll")
    public FeatureResponse getFeatures() {
        return featureService.getFeatures();
    }

    @PostMapping("/create")
    public ResponseEntity<?> createFeature(@RequestBody FeatureCreateRequest featureCreateRequest) {
        return featureService.createFeature(featureCreateRequest);
    }

}
