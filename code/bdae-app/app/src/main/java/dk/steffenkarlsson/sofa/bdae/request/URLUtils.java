package dk.steffenkarlsson.sofa.bdae.request;

import dk.steffenkarlsson.sofa.bdae.extra.ConfigurationHandler;
import dk.steffenkarlsson.sofa.networking.URLBuilder;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class URLUtils {

    private static ConfigurationHandler mHandler = ConfigurationHandler.getInstance();

    private static URLBuilder apiBuilder(String target) {
        return new URLBuilder().subdomain("/api" + target);
    }

    private static URLBuilder instanceBuilder(String target) {
        return apiBuilder("/" + mHandler.getInstanceName()).subdomain(String.format("/%s", target));
    }

    private static String build(URLBuilder builder) {
        return builder.build("http://" + mHandler.getApiHostName());
    }

    public static String initializeWithInstanceUrl() {
        return build(apiBuilder("/initialize")
                .addParameter("instance-name", mHandler.getInstanceName())
                .addParameter("identifier", mHandler.getGateway(false)));
    }

    public static String getDatasetsUrl() {
        return build(instanceBuilder("get_datasets"));
    }
}
