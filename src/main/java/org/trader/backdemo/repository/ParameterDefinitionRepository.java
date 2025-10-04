package org.trader.backdemo.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.trader.backdemo.entity.ParameterDefinitionEntity;

import java.util.Optional;

@Repository
public interface ParameterDefinitionRepository extends JpaRepository<ParameterDefinitionEntity, Long> {

    @Query("select p from ParameterDefinitionEntity p where p.feature.id = :featureId and p.name = :name")
    Optional<ParameterDefinitionEntity> findByFeatureIdAndName(@Param("featureId") Long featureId,
                                                               @Param("name") String name);

}

