package org.trader.backdemo.service;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.trader.backdemo.dto.request.AgentFormRequest;
import org.trader.backdemo.dto.response.AgentsPerUserResponse;
import org.trader.backdemo.entity.*;
import org.trader.backdemo.mapper.AgentEntityMapper;
import org.trader.backdemo.repository.AgentRepository;
import org.trader.backdemo.repository.FeatureRepository;
import org.trader.backdemo.repository.ParameterDefinitionRepository;
import org.trader.backdemo.repository.UserRepository;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

@RequiredArgsConstructor
@Service
public class AgentService {

    private final AgentRepository agentRepository;
    private final UserRepository userRepository;
    private final AgentEntityMapper agentEntityMapper;
    private final FeatureRepository featureRepository;
    private final ParameterDefinitionRepository parameterDefinitionRepository;

    public ResponseEntity<Boolean> createAgent(AgentFormRequest agentFormRequest, Long userId) {
        try {
            AgentEntity agent = new AgentEntity();
            BeanUtils.copyProperties(agentFormRequest, agent);

            if (userId != null) {
                UserEntity user = userRepository.findById(userId).orElse(null);
                agent.setUser(user);
            }

            // Construire les features à partir du payload
            Set<AgentFeatureEntity> agentFeatures = new HashSet<>();
            Map<String, Map<String, String>> featuresPayload = agentFormRequest.getFeatures();
            if (featuresPayload != null && !featuresPayload.isEmpty()) {
                for (Map.Entry<String, Map<String, String>> featureEntry : featuresPayload.entrySet()) {
                    String featureName = featureEntry.getKey();
                    FeatureEntity feature = featureRepository.findByNameWithParameters(featureName)
                            .orElseThrow(() -> new IllegalArgumentException("Feature inconnue: " + featureName));

                    AgentFeatureEntity af = new AgentFeatureEntity();
                    af.setAgent(agent);
                    af.setFeature(feature);

                    Set<ParameterValueEntity> values = new HashSet<>();
                    Map<String, String> params = featureEntry.getValue();
                    if (params != null) {
                        for (Map.Entry<String, String> p : params.entrySet()) {
                            String paramName = p.getKey();
                            String paramValue = p.getValue();

                            ParameterDefinitionEntity def = parameterDefinitionRepository
                                    .findByFeatureIdAndName(feature.getId(), paramName)
                                    .orElseThrow(() -> new IllegalArgumentException(
                                            "Paramètre inconnu '" + paramName + "' pour la feature '" + featureName + "'"));

                            ParameterValueEntity pv = new ParameterValueEntity();
                            pv.setAgentFeature(af);
                            pv.setParameterDefinition(def);
                            pv.setValue(paramValue);
                            values.add(pv);
                        }
                    }
                    af.setParameterValues(values);
                    agentFeatures.add(af);
                }
            }
            agent.setAgentFeatures(agentFeatures);

            agentRepository.save(agent);
            return ResponseEntity.ok(true);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(false);
        }
    }

    @Transactional(readOnly = true)
    public ResponseEntity<List<AgentsPerUserResponse>> agentsByUserId(Long userId) {
        try {
            List<AgentEntity> entities = agentRepository.findByUserId(userId);
            List<AgentsPerUserResponse> responses = agentEntityMapper.toResponseList(entities);
            return ResponseEntity.ok(responses);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }

    }
}