package org.trader.backdemo.controller;

import org.springframework.web.bind.annotation.*;
import org.trader.backdemo.service.FeatureService;
import org.trader.backdemo.dto.response.*;

@RestController
@RequestMapping("/api")
public class FeatureController {

    private final FeatureService featureService;


    public FeatureController(FeatureService featureService) {
        this.featureService = featureService;
    }

    @GetMapping("/features")
    public FeatureResponse getFeatures(){
        return featureService.getFeatures();
    }
    

}
