package dk.steffenkarlsson.sofa.networking;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;


public class RequestUtils {

    private static Gson mGson = new GsonBuilder().setDateFormat("yyyy-MM-dd'T'HH:mm:ssZ").create();

    /**
     * @param token The syntax for token is: new TypeToken<T>(){}
     * @throws ParserException
     */
    public static <T> T parse(TypeToken<T> token, String body) throws ParserException {
        return parse(token.getType(), body);
    }

    public static <T> T parse(Type classType, String body) throws ParserException {
        try {
            return mGson.fromJson(body, classType);
        } catch (Exception e) {
            throw new ParserException(e.getMessage());
        }
    }

    public static <T> String parse(T body) {
        return mGson.toJson(body);
    }

}