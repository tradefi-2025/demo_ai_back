package org.trader.backdemo.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import org.trader.backdemo.entity.FeatureEntity;

import java.util.List;

@Repository
public interface FeatureRepository extends JpaRepository<FeatureEntity, Long> {
    @Query("SELECT f FROM FeatureEntity f LEFT JOIN FETCH f.parametreDefinitions")
    List<FeatureEntity> findAllWithParameters();
}
