package org.trader.backdemo.service;


import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.trader.backdemo.dto.request.UserInscriptionRequest;
import org.trader.backdemo.dto.response.LogInReponse;
import org.trader.backdemo.entity.UserEntity;
import org.trader.backdemo.exception.domaine.ExistingUserException;
import org.trader.backdemo.repository.UserRepository;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

import java.util.Optional;


@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private BCryptPasswordEncoder passwordEncoder;


    public ResponseEntity<String> inscription(UserInscriptionRequest userInscriptionRequest)
            throws ExistingUserException {
        if (userRepository.existsByEmail(userInscriptionRequest.getEmail())) {
            throw new ExistingUserException("Email already exists");
        }


        UserEntity userEntity = new UserEntity();
        userEntity.setEmail(userInscriptionRequest.getEmail());
        userEntity.setName(userInscriptionRequest.getName());
        userEntity.setPassword(passwordEncoder.encode(userInscriptionRequest.getPassword()));


        userRepository.save(userEntity);

        return ResponseEntity.ok().body("Account has created successfully");


    }


    public ResponseEntity<?> getMe(Long userId) {
        Optional<UserEntity> userEntityOptional = userRepository.findById(userId);
        if (userEntityOptional.isPresent()) {
            return ResponseEntity.ok().body(
                    LogInReponse.builder().userId(userEntityOptional.get().getId())
                            .email(userEntityOptional.get().getEmail())
                            .name(userEntityOptional.get().getName())
                            .build()
            );
        }
        return ResponseEntity.notFound().build();
    }
}
