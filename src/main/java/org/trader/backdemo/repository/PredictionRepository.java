package org.trader.backdemo.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import org.trader.backdemo.entity.PredictionEntity;

import java.util.List;

@Repository
public interface PredictionRepository extends JpaRepository<PredictionEntity, Long> {

    List<PredictionEntity> findByAgentIdIn(List<Long> agentIds);
}
