package org.trader.backdemo.service;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.stereotype.Service;
import org.trader.backdemo.dto.request.UserLoginRequest;
import org.trader.backdemo.dto.response.LogInReponse;
import org.trader.backdemo.entity.UserEntity;
import org.trader.backdemo.repository.UserRepository;
import org.trader.backdemo.service.security.JwtService;

import java.util.Optional;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final AuthenticationManager authenticationManager;
    private final JwtService jwtService;

    public ResponseEntity<?> signIn(UserLoginRequest userLoginRequest) throws BadCredentialsException {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(userLoginRequest.getEmail(), userLoginRequest.getPassword())
        );


        Optional<UserEntity> foundedUser = userRepository.findByEmail(userLoginRequest.getEmail());
        if (foundedUser.isEmpty()) {
            throw new BadCredentialsException(userLoginRequest.getEmail() + " - Invalid email");
        }
        UserEntity userObj = foundedUser.get();

        LogInReponse ResponseBody = LogInReponse.builder()
                .userId(userObj.getId())
                .name(userObj.getName())
                .email(userObj.getEmail())
                .build();


        ResponseCookie responseJwtCookie = jwtService.getResponseCookie(userObj);

        return ResponseEntity.ok().header(HttpHeaders.SET_COOKIE, responseJwtCookie.toString()).body(ResponseBody);

    }


    public ResponseEntity<?> logOutUser() {
        ResponseCookie cookie = jwtService.getCleanJwtCookie();
        return ResponseEntity.ok().header(HttpHeaders.SET_COOKIE, cookie.toString()).body("Logout successful");
    }
}
