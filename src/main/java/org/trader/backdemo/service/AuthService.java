package org.trader.backdemo.service;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.trader.backdemo.dto.request.UserLoginRequest;
import org.trader.backdemo.dto.response.LogInReponse;
import org.trader.backdemo.dto.session.SessionUser;
import org.trader.backdemo.entity.UserEntity;
import org.trader.backdemo.repository.UserRepository;

import java.util.Optional;

@Service
public class AuthService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private BCryptPasswordEncoder passwordEncoder;

    public ResponseEntity<LogInReponse> signIn(UserLoginRequest userLoginRequest, HttpServletRequest httpRequest) throws BadCredentialsException {

        Optional<UserEntity> foundedUser = userRepository.findByEmail(userLoginRequest.getEmail());
        if (foundedUser.isEmpty())
            throw new BadCredentialsException(userLoginRequest.getEmail() + "-  Invalid email");
        UserEntity userObj = foundedUser.get();

        if(!passwordEncoder.matches(userLoginRequest.getPassword(), userObj.getPassword())){
            throw new BadCredentialsException("Wrong password");
        }

        SessionUser sessionUser = SessionUser.builder()
                .userId(userObj.getId())
                .email(userObj.getEmail())
                .name(userObj.getName())
                .build();

        HttpSession session = httpRequest.getSession(true);
        session.setAttribute("user", sessionUser);
        session.setMaxInactiveInterval(3600000);



        return ResponseEntity.ok().body(
                LogInReponse.builder()
                        .userId(userObj.getId())
                        .name(userObj.getName())
                        .build());
    }


    public ResponseEntity<Boolean> authentificaitonCheck(HttpServletRequest request) {

        HttpSession session = request.getSession(false);
        if (session == null)
            return ResponseEntity.ok(false);

        SessionUser sessionUser = (SessionUser) session.getAttribute("user");
        return ResponseEntity.ok(sessionUser != null);
    }

    public ResponseEntity<String> logOutUser(HttpServletRequest request) {

        HttpSession session = request.getSession(false);
        if (session != null)
            session.invalidate();
        return ResponseEntity.ok("User logged out");

    }
}
