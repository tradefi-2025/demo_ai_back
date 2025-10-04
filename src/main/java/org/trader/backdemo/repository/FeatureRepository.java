package org.trader.backdemo.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.trader.backdemo.entity.FeatureEntity;

import java.util.List;
import java.util.Optional;

@Repository
public interface FeatureRepository extends JpaRepository<FeatureEntity, Long> {
    @Query("SELECT f FROM FeatureEntity f LEFT JOIN FETCH f.parameterDefinitions")
    List<FeatureEntity> findAllWithParameters();


    @Query("SELECT f FROM FeatureEntity f LEFT JOIN FETCH f.parameterDefinitions WHERE f.name = :name")
    Optional<FeatureEntity> findByNameWithParameters(@Param("name") String name);
}
