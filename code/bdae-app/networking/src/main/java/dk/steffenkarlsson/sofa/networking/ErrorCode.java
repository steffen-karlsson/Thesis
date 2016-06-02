package dk.steffenkarlsson.sofa.networking;

/**
 * Created by steffenkarlsson on 23/12/14.
 */
@SuppressWarnings("ALL")
public enum ErrorCode {
    PARSER_FAIL(99), NO_BODY(98), NO_NETWORK(97), NETWORK_ERROR(96);

    public int code;

    ErrorCode(int code) {
        this.code = code;
    }
}
