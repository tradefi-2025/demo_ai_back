package org.trader.backdemo.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.trader.backdemo.dto.response.AgentFeatureResponse;
import org.trader.backdemo.dto.response.AgentsPerUserResponse;
import org.trader.backdemo.dto.response.ParameterValueResponse;
import org.trader.backdemo.entity.AgentEntity;
import org.trader.backdemo.entity.AgentFeatureEntity;
import org.trader.backdemo.entity.ParameterValueEntity;

import java.util.List;
import java.util.Set;

@Mapper(componentModel = "spring")
public interface AgentEntityMapper {

    @Mapping(target = "agentFeatures", source = "agentFeatures")
    AgentsPerUserResponse toResponse(AgentEntity entity);

    List<AgentsPerUserResponse> toResponseList(List<AgentEntity> entities);

    @Mapping(target = "featureId", source = "feature.id")
    @Mapping(target = "featureName", source = "feature.name")
    @Mapping(target = "featureDescription", source = "feature.description")
    @Mapping(target = "parameters", source = "parameterValues")
    AgentFeatureResponse toFeatureResponse(AgentFeatureEntity entity);

    Set<AgentFeatureResponse> toFeatureResponseSet(Set<AgentFeatureEntity> entities);

    @Mapping(target = "name", source = "parameterDefinition.name")
    @Mapping(target = "type", source = "parameterDefinition.type")
    @Mapping(target = "defaultValue", source = "parameterDefinition.defaultValue")
    @Mapping(target = "required", source = "parameterDefinition.required")
    ParameterValueResponse toParameterValueResponse(ParameterValueEntity entity);

    Set<ParameterValueResponse> toParameterValueResponseSet(Set<ParameterValueEntity> entities);
}
