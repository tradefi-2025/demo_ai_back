package org.trader.backdemo.service;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.context.SecurityContextRepository;
import org.springframework.stereotype.Service;
import org.trader.backdemo.dto.request.UserLoginRequest;
import org.trader.backdemo.dto.response.LogInReponse;
import org.trader.backdemo.dto.session.SessionUser;
import org.trader.backdemo.entity.UserEntity;
import org.trader.backdemo.repository.UserRepository;

import java.util.Optional;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final AuthenticationManager authenticationManager;
    private final SecurityContextRepository securityContextRepository;

    public ResponseEntity<LogInReponse> signIn(UserLoginRequest userLoginRequest, HttpServletRequest httpRequest, HttpServletResponse httpResponse) throws BadCredentialsException {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        userLoginRequest.getEmail(),
                        userLoginRequest.getPassword()
                )
        );

        // Crée et sauvegarde le SecurityContext en session (JSESSIONID)
        SecurityContext context = SecurityContextHolder.createEmptyContext();
        context.setAuthentication(authentication);
        SecurityContextHolder.setContext(context);
        securityContextRepository.saveContext(context, httpRequest, httpResponse);

        Optional<UserEntity> foundedUser = userRepository.findByEmail(userLoginRequest.getEmail());
        if (foundedUser.isEmpty())
            throw new BadCredentialsException(userLoginRequest.getEmail() + " - Invalid email");
        UserEntity userObj = foundedUser.get();

        HttpSession session = httpRequest.getSession(true);

        SessionUser sessionUser = SessionUser.builder()
                .userId(userObj.getId())
                .email(userObj.getEmail())
                .name(userObj.getName())
                .build();
        session.setAttribute("user", sessionUser);

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
        SecurityContextHolder.clearContext();
        return ResponseEntity.ok("User logged out");
    }
}
