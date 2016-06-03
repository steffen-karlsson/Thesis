package dk.steffenkarlsson.sofa.networking;

import java.io.IOException;

/**
 * Created by steffenkarlsson on 22/12/14.
 */
@SuppressWarnings("ALL")
public class ParserException extends IOException {

    public ParserException(String detailMessage) {
        super(detailMessage);
    }

    public ParserException() {
    }
}