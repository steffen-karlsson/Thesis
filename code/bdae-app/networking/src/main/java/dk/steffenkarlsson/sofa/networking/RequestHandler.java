package dk.steffenkarlsson.sofa.networking;

import java.util.HashMap;
import java.util.Map;

/**
 * Created by steffenkarlsson on 23/12/14.
 */
@SuppressWarnings("ALL")
public class RequestHandler {

    private static int mCounter = 0;
    private static Map<Enum, Integer> mRequestMap = new HashMap<>();
    private static Map<Integer, Enum> mInversedRequestMap = new HashMap<>();

    protected static int getIdFromRequestIdentifier(Enum requestIdentifier) {
        if (mRequestMap.containsKey(requestIdentifier))
            return mRequestMap.get(requestIdentifier);

        mCounter++;
        int count = mCounter;
        mRequestMap.put(requestIdentifier, count);
        mInversedRequestMap.put(count, requestIdentifier);

        return count;
    }

    public static <E extends Enum> E getRequestIdentifierFromId(int internalId) {
        if (mInversedRequestMap.containsKey(internalId)) {
            return (E)mInversedRequestMap.get(internalId);
        }

        return null;
    }
}
