package org.trader.backdemo.service;


import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.trader.backdemo.dto.response.FeatureResponse;
import org.trader.backdemo.mapper.FeatureEntityMapper;
import org.trader.backdemo.models.Feature;
import org.trader.backdemo.repository.FeatureRepository;


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
}
