package org.trader.backdemo.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;
import org.trader.backdemo.entity.FeatureEntity;
import org.trader.backdemo.entity.ParameterDefinitionEntity;
import org.trader.backdemo.models.Feature;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

@Mapper(componentModel = "spring")
public interface FeatureEntityMapper {

    @Mapping(source = "parameterDefinitions", target = "parameters", qualifiedByName = "toParametersMap")
    Feature toFeature(FeatureEntity featureEntity);

    @Named("toParametersMap")
    default Map<String, String> toParametersMap(Set<ParameterDefinitionEntity> paramDefs) {
        Map<String, String> params = new HashMap<>();
        if (paramDefs == null) {
            return params;
        }
        for (ParameterDefinitionEntity def : paramDefs) {
            params.put(def.getName(), def.getDefaultValue());
        }
        return params;
    }
}
