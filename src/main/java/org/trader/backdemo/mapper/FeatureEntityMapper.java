package org.trader.backdemo.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;
import org.trader.backdemo.dto.response.ParameterDefinitionResponse;
import org.trader.backdemo.entity.FeatureEntity;
import org.trader.backdemo.entity.ParameterDefinitionEntity;
import org.trader.backdemo.models.Feature;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Mapper(componentModel = "spring")
public interface FeatureEntityMapper {

    @Mapping(source = "parameterDefinitions", target = "parameters", qualifiedByName = "toParametersMap")
    Feature toFeature(FeatureEntity featureEntity);

    @Named("toParametersMap")
    default Map<String, ParameterDefinitionResponse> toParametersMap(Set<ParameterDefinitionEntity> paramDefs) {
        Map<String, ParameterDefinitionResponse> params = new HashMap<>();
        if (paramDefs == null) {
            return params;
        }
        for (ParameterDefinitionEntity def : paramDefs) {
            params.put(def.getName(), toParameterDefinitionResponse(def));
        }
        return params;
    }

    default ParameterDefinitionResponse toParameterDefinitionResponse(ParameterDefinitionEntity def) {
        ParameterDefinitionResponse response = new ParameterDefinitionResponse();
        response.setName(def.getName());
        response.setDefaultValue(def.getDefaultValue());
        response.setDescription(def.getDescription());
        response.setMinValue(def.getMinValue());
        response.setMaxValue(def.getMaxValue());
        response.setType(def.getType() == null ? null : def.getType().name());
        response.setEnumValues(toList(def.getEnumValues()));
        response.setFileName(def.getFileName());
        response.setRequired(def.isRequired());
        return response;
    }

    default List<String> toList(String[] values) {
        return values == null ? null : Arrays.asList(values);
    }
}
