package org.trader.backdemo.service.client;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.trader.backdemo.dto.external.ExternalPredictionRequest;
import org.trader.backdemo.dto.external.ExternalPredictionResponse;

@Component
public class PredictionFeignClient {

    private final RestTemplate restTemplate;
    private final String predictionUrl;

    public PredictionFeignClient(RestTemplate restTemplate,
                                 @Value("${ms.prediction.url}") String predictionUrl) {
        this.restTemplate = restTemplate;
        this.predictionUrl = predictionUrl;
    }

    public ResponseEntity<ExternalPredictionResponse> predictExternal(ExternalPredictionRequest body) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<ExternalPredictionRequest> entity = new HttpEntity<>(body, headers);

        return restTemplate.exchange(
                predictionUrl,
                HttpMethod.POST,
                entity,
                ExternalPredictionResponse.class
        );
    }
}
