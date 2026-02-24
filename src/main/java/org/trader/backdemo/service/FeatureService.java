package org.trader.backdemo.service;


import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.trader.backdemo.dto.request.FeatureCreateRequest;
import org.trader.backdemo.dto.response.FeatureResponse;
import org.trader.backdemo.entity.FeatureEntity;
import org.trader.backdemo.entity.ParameterDefinitionEntity;
import org.trader.backdemo.mapper.FeatureEntityMapper;
import org.trader.backdemo.models.Feature;
import org.trader.backdemo.repository.FeatureRepository;

import java.util.stream.Collectors;


@RequiredArgsConstructor
@Service
public class FeatureService {

    private final FeatureRepository featureEntityRepository;
    private final FeatureEntityMapper featureEntityMapper;

    @Transactional(readOnly = true)
    public FeatureResponse getFeatures() {

        return FeatureResponse.
                builder().
                features(featureEntityRepository.findAllWithParameters().stream()
                        .map(featureEntityMapper::toFeature)
                        .toArray(Feature[]::new))
                .build();
    }

    public ResponseEntity<?> createFeature(FeatureCreateRequest featureCreateRequest) {

        FeatureEntity featureEntity = new FeatureEntity();
        featureEntity.setName(featureCreateRequest.name());
        featureEntity.setDescription(featureCreateRequest.description());
        if (featureCreateRequest.parameterDefinitionRequest() != null) {
            featureEntity.setParameterDefinitions(featureCreateRequest.parameterDefinitionRequest().stream()
                    .map(paramReq -> {
                        ParameterDefinitionEntity parameterDefinitionEntity = new ParameterDefinitionEntity();
                        parameterDefinitionEntity.setName(paramReq.name());
                        parameterDefinitionEntity.setFeature(featureEntity);
                        parameterDefinitionEntity.setDefaultValue(paramReq.defaultValue());
                        parameterDefinitionEntity.setDescription(paramReq.description());
                        parameterDefinitionEntity.setType(ParameterDefinitionEntity.parameterTypeEnum.valueOf(paramReq.type().toUpperCase()));
                        return parameterDefinitionEntity;
                    }).collect(Collectors.toSet())
            );
        }
        featureEntityRepository.save(featureEntity);
        return ResponseEntity.ok().body(featureEntity);
    }
}
