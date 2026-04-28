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

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
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

    @Transactional
    public ResponseEntity<?> createFeature(FeatureCreateRequest featureCreateRequest) {
        List<FeatureEntity> existingFeatures = featureEntityRepository.findAllByNameWithParameters(featureCreateRequest.name());

        FeatureEntity featureEntity = existingFeatures.isEmpty() ? new FeatureEntity() : existingFeatures.getFirst();
        featureEntity.setName(featureCreateRequest.name());
        featureEntity.setDescription(featureCreateRequest.description());

        Set<ParameterDefinitionEntity> parameterDefinitions = buildParameterDefinitions(featureCreateRequest, featureEntity);
        featureEntity.getParameterDefinitions().clear();
        featureEntity.getParameterDefinitions().addAll(parameterDefinitions);

        if (existingFeatures.size() > 1) {
            featureEntityRepository.deleteAll(existingFeatures.subList(1, existingFeatures.size()));
        }

        FeatureEntity savedFeature = featureEntityRepository.save(featureEntity);
        return ResponseEntity.ok().body(featureEntityMapper.toFeature(savedFeature));
    }

    @Transactional
    public ResponseEntity<Void> deleteFeature(String name) {
        List<FeatureEntity> existingFeatures = featureEntityRepository.findAllByNameWithParameters(name);
        if (existingFeatures.isEmpty()) {
            return ResponseEntity.notFound().build();
        }
        featureEntityRepository.deleteAll(existingFeatures);
        return ResponseEntity.noContent().build();
    }

    private Set<ParameterDefinitionEntity> buildParameterDefinitions(FeatureCreateRequest featureCreateRequest,
                                                                     FeatureEntity featureEntity) {
        if (featureCreateRequest.parameterDefinitionRequest() == null) {
            return new LinkedHashSet<>();
        }
        return featureCreateRequest.parameterDefinitionRequest().stream()
                .map(paramReq -> {
                    ParameterDefinitionEntity parameterDefinitionEntity = new ParameterDefinitionEntity();
                    parameterDefinitionEntity.setName(paramReq.name());
                    parameterDefinitionEntity.setFeature(featureEntity);
                    parameterDefinitionEntity.setDefaultValue(paramReq.defaultValue());
                    parameterDefinitionEntity.setDescription(paramReq.description());
                    parameterDefinitionEntity.setMinValue(paramReq.minValue());
                    parameterDefinitionEntity.setMaxValue(paramReq.maxValue());
                    parameterDefinitionEntity.setEnumValues(toArray(paramReq.enumValues()));
                    parameterDefinitionEntity.setFileName(paramReq.fileName());
                    parameterDefinitionEntity.setRequired(paramReq.required());
                    parameterDefinitionEntity.setType(ParameterDefinitionEntity.parameterTypeEnum.valueOf(paramReq.type().toUpperCase()));
                    return parameterDefinitionEntity;
                })
                .collect(Collectors.toCollection(LinkedHashSet::new));
    }

    private String[] toArray(List<String> values) {
        return values == null ? null : values.toArray(String[]::new);
    }
}
