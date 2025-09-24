package org.trader.backdemo.service;

    import lombok.NoArgsConstructor;
    import org.springframework.beans.BeanUtils;
    import org.springframework.beans.factory.annotation.Autowired;
    import org.springframework.http.HttpStatus;
    import org.springframework.http.ResponseEntity;
    import org.springframework.stereotype.Service;
    import org.trader.backdemo.dto.request.AgentFormRequest;
    import org.trader.backdemo.entity.AgentEntity;
    import org.trader.backdemo.repository.AgentRepository;

    @NoArgsConstructor
    @Service
    public class AgentService {

        @Autowired
        private AgentRepository agentRepository;

        public ResponseEntity<Boolean> createAgent(AgentFormRequest agentFormRequest) {
            try {
                AgentEntity entity = new AgentEntity();
                BeanUtils.copyProperties(agentFormRequest, entity);
                agentRepository.save(entity);
                return ResponseEntity.ok(true);
            } catch (Exception e) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(false);
            }
        }
    }